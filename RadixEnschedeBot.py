# @author Wouter van Harten <wouter@woutervanharten.nl>
import copy
import json
import os
import re
import sys
import traceback
import urllib
from pathlib import Path
from random import randrange as randint

import requests
from dateutil.parser import parse
from requests.exceptions import ConnectionError

from NumericStringParser import NumericStringParser
from Product import Product
from Purchase import Purchase
from User import User
from daemon import runner
from dbhelper import DBHelper


class RadixEnschedeBot:
    db = None
    TOKEN = ""
    URL = "https://api.telegram.org/bot{}/".format(TOKEN)
    ADMIN = 0

    help_text = """
    === Basic commands ===
    (commands marked with "*" will be answered privately)
    /help * --- shows all commands.
    
    /info * --- some info about Tally
    /nick henk  --- change your nickname in this group to "henk" (max 12 letters).
    /nicks  --- overview of all nicknames 
    /products  --- overview of all added products
    /all_tallies  --- overview of all tallies
    /tallies * --- overview of your tallies
    /debtors --- list of people with a positive amount of (normal) tallies.
    /add grolschbier  --- add a product named "grolschbier" (max 12 letters)
    /all_history 10  --- show last 10 transactions (default 5, max. 99)
    /history 5 * --- show last 5 transactions by you (default 10, max. 99)
    /thanks henk  --- give henk a tally to thank him for something. (-1 for henk +1 for you)
    
    === Tally-ing ===
    You can Tally positivly and negatively between 1 and 99 
    Examples:
    +1  --- add one tally 
    16  --- add 16 tallies 
    -4  --- remove 4 tallies
    
    You can also tally some specific product
    Example:
    +1 coke  --- add one coke
    
    You can also tally some for someone else
    Example:
    sjaak 5  --- add 5 tallies for sjaak
    
    You can also tally some specific product for someone else
    Example:
    sjaak -3 beer  --- remove 3 beers for sjaak
    
    === STFU Tally ===
    If you start your sentence with a dot, Tally will ignore it.
    Example
    . hey Tally! Tally! hey Tally! TALLY!!!"""

    info_text = """Tally is a simple Telegram-bot He is created because someone was to lazy to stand up and tally his 
    beer. This someone rather preferred program a complete Telegram-bot. You're free to use Tally for your own 
    purposes, however Tally is confronted with alcoholic beverages on a regular basis. Therefore Tally, 
    nor it's maker can guarantee that Tally is and will stay functioning at a socially acceptable level. Honestly, 
    we wouldn't be surprised if Tally would get Korsakoff, or have some troubles with (temporary) black-outs. Let 
    alone that he stays alive. 
    
    - Wouter (tally@woutervanharten.nl)"""

    NOT_WHITESPACE = re.compile(r'[^s]')

    def __init__(self):
        self.stdin_path = '/dev/null'
        self.stdout_path = '/home/wouter/tally_out'
        self.stderr_path = '/home/wouter/tally_err'
        self.pidfile_path = '/tmp/tally.pid'
        self.pidfile_timeout = 5
        self.db = DBHelper()
        with open("config.json", "r") as data_file:
            data = json.load(data_file)
        self.ADMIN = data['ADMIN']
        self.TOKEN = data['TOKEN']
        self.URL = "https://api.telegram.org/bot{}/".format(self.TOKEN)

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self, offset=None):
        url = self.URL + "getUpdates?timeout=1000"
        if offset:
            url += "&offset={}".format(offset)
        js = self.get_json_from_url(url)
        return js

    def get_last_chat_id_and_text(self, updates):
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return (text, chat_id)

    def get_last_update_id(self, updates):
        update_ids = []
        for update in updates["result"]:
            update_ids.append(int(update["update_id"]))
        return max(update_ids)

    def send_message(self, text, chat_id, reply_markup=None):
        text = urllib.parse.quote_plus(text)
        url = self.URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
        if reply_markup:
            url += "&reply_markup={}".format(reply_markup)
        self.get_url(url)

    def run(self):
        last_update_id = None
        while True:
            try:
                updates = self.get_updates(last_update_id)
                if "result" in updates:
                    if len(updates["result"]) > 0:
                        last_update_id = self.get_last_update_id(updates) + 1
                        self.extract_messages(updates)
            except ConnectionError as e:
                continue
            json_path = os.path.dirname(os.path.abspath(__file__)) + '/post.json';
            jsonFile = Path(json_path)
            print(jsonFile.is_file())
            if jsonFile.is_file():
                with open(json_path, 'r') as f:
                    data = f.read().replace('\n', '')
                    for tallyPost in self.decode_stacked(data):
                        x = tallyPost["amount"] + " " + tallyPost["product"]
                        self.handle_message(tallyPost["group"], x, tallyPost["user"], "", 'group')
                    f.close()
                os.remove(json_path)

    def decode_stacked(self, document, pos=0, decoder=json.JSONDecoder()):
        while True:
            match = self.NOT_WHITESPACE.search(document, pos)
            if not match:
                return
            pos = match.start()

            try:
                obj, pos = decoder.raw_decode(document, pos)
            except json.JSONDecodeError:
                # do something sensible if there's some error
                raise
            yield obj

    def extract_messages(self, updates):
        for update in updates["result"]:
            try:
                text = update["message"]["text"]
                chat = update["message"]["chat"]["id"]
                telegram_id = update["message"]["from"]["id"]
                name = update["message"]["from"]["first_name"]
                type = update["message"]["chat"]["type"]
                self.handle_message(chat, text, telegram_id, name, type)

            except Exception as e:
                print(e)
                traceback.print_stack()
                print(update)
                print("")

    def personal_message(self, chat, text, telegram_id, name):
        if str(telegram_id) != str(self.ADMIN):
            self.send_message("Add me to a group :)", telegram_id)
            return

        split_text = text.split()
        switcher = {
            '/add_chat': self.add_chat
        }
        fun = switcher.get(split_text[0], self.command_not_found)
        fun(chat, split_text, telegram_id)

    def add_chat(self, chat, split_text, telegram_id):
        self.db.add_chat(int(split_text[1]))
        self.send_message("Added " + str(split_text[1]), self.ADMIN)

    def handle_message(self, chat, text, telegram_id, name, type):
        text = text.lower()

        # Check if in group
        if type != 'group' and type != 'supergroup':
            self.personal_message(chat, text, telegram_id, name)
            return
        # Check if chat allowed
        if not self.db.check_chat(chat):
            self.send_message("Ask Wouter van Harten (+31)6 833 24 277 to whitelist <" + str(chat) + ">", chat)
            self.send_message(
                "Activity from unknown chat <" + str(chat) + ">, maybe you can whitelist it with '/add_chat " + str(
                    chat) + "' ?", self.ADMIN)
            return

        # Check for STFU
        if text[0] == ".":
            return
        # Check for command
        if text[0] == '/':
            self.handle_command(chat, text, telegram_id)
            return

        split_text = text.split()

        nsp = NumericStringParser()
        try:
            int(nsp.eval(split_text[0]).real)
            self.tally(split_text, chat, telegram_id, name)
            return
        except Exception as e:
            print(e)

        # Try for username
        user = self.db.get_user_by_name(chat, split_text[0])
        if user != False:
            del split_text[0]
            try:
                int(nsp.eval(split_text[0]).real)
                self.tally(split_text, chat, user.telegram_id, split_text[0], False)
                return
            except Exception:
                self.send_message("unknown amount: " + split_text[0], chat)
                pass
            return
        self.send_message("Que? (" + text + ")", chat)

    def tally(self, split_text, chat, telegram_id, name, make_new_user=True):
        nsp = NumericStringParser()
        # We only drink an integer amount of real beer
        amount = int(nsp.eval(split_text[0]).real)
        if abs(amount) > 99:
            self.send_message("Tally between -100 and 100, " + str(amount) + " given", chat)
            return
        if abs(amount) < 0.5:
            self.send_message("That's a bunch of nothing you have there", chat)
            return
        user = self.db.get_user_by_telegram_id(telegram_id)
        if (not make_new_user) & (user == False):
            self.send_message("Unknown user: " + name, chat)
            return
        if user is False:
            user = User(name.lower(), telegram_id)
            user.groups.append(self.db.get_chat(chat))
            self.db.add_user(user)
        if self.db.get_chat(chat) not in user.groups and make_new_user:
            user.groups.append(self.db.get_chat(chat))
        user = self.db.get_user_by_telegram_id(telegram_id)
        if len(split_text) < 2:
            product = self.db.get_chat(chat).products[0]
        else:
            product = self.db.get_product_by_name(chat, split_text[1])
            if product is None:
                self.send_message("Unknown product: " + split_text[1], chat)
                return
        purchase = Purchase(user, product, amount, self.db.get_chat(chat))
        # Get old score and new score
        all_tallies = self.db.get_all_tallies(chat, user)
        if product.name in all_tallies.keys():
            new_score = copy.copy(all_tallies[product.name])
            old_score = new_score - amount
        else:
            old_score = 0
            new_score = amount
        # Tallied and balance message:
        message = "Tallied {1!s} {3!s} for {0!s} (current balance is {2!s} {3!s}).".format(user.name, amount, new_score,
                                                                                           product.name)
        # Attach some additional message if called for If user remains on the wrong end with a positive tally,
        # add a simple notification & sometimes a personal message:
        if (old_score >= 0) and (new_score > 0) and (amount > 0):
            message += "\n{0!s} has run out of {3!s} and is consuming another person's {3!s}!".format(user.name, amount,
                                                                                                      new_score,
                                                                                                      product.name)
            # Every fourth product or tally of at least 4 products, remind the user personally
            if new_score % 4 == 0:
                self.snark(user, new_score, product)
            elif amount >= 4:
                self.snark(user, new_score, product)
        # If a user remains on the wrong end with a negative tally, a more encouraging message:
        elif (old_score >= 0) and (new_score > 0) and (amount < 0):
            message += "\n{0!s}, thank you for adding some {3!s} to your stock. You did not add enough to return to " \
                       "Tally's good graces, though!".format(
                user.name, amount, new_score, product.name)
        # Notify those who add exactly enough:
        elif (old_score >= 0) and (new_score == 0) and (amount < 0):
            message += "\n{0!s}, thank you for adding some {3!s} to your stock. Tally likes those who do their " \
                       "bookkeeping to the letter!".format(
                user.name, amount, new_score, product.name)
        # Warn a user if their last item is tallied:
        elif (old_score < 0) and (new_score >= 0):
            message += "\nBetter enjoy that {3!s}, {0!s}! You've depleted your stock!".format(user.name, amount,
                                                                                              new_score, product.name)
            self.send_message(
                "{0!s}, your last {3!s} was just tallied!".format(user.name, amount, new_score, product.name),
                telegram_id)
        # Send message & commit purchase to database
        self.send_message(message, chat)
        self.db.add_purchase(purchase)
        return

    def snark(self, user, new_score, product):
        # Unpack input
        productname = product.name
        telegram_id, username = user.telegram_id, user.name
        # Messages
        messages = [
            "Beste {0!s}, ter ere van deze speciale gelegenheid wil ik graag iets van de wijsheid van onze voormalige "
            "koningin met je delen:\n'Hee majesteit, ga eens {1!s} halen!'".format(
                username, productname),
            "Beste {0!s}, wat advies: {1!s} {2!s} schuld is {1!s} {2!s} schuld teveel!".format(username, new_score,
                                                                                               productname),
            "Beste {0!s}, wist je dat Albert Heijn XL tot 22:00 open is en ze daar {2!s} hebben?".format(username,
                                                                                                         new_score,
                                                                                                         productname),
            "Beste {0!s}, voor jou is het geen {2!s}tijd, maar supermarkttijd!".format(username, new_score,
                                                                                       productname),
            "Je creëert nu een {2!s}probleem, en nee dat is geen poar neem".format(username, new_score, productname),
            "2 woorden, {3!s} letters: {2!s} halen!".format(username, new_score, productname, len(productname) + 5)]
        # Random integer
        i = randint(0, len(messages))
        message = messages[i]
        # Alexcheck
        if (new_score > 19):
            extra_message = "\n\nOverweeg alsjeblieft het volgende zelfhulp nummer te bellen: Alex bierservice " \
                            "053-4338460 "
            message += extra_message
        else:
            extra_message = "\n\nRaadpleeg je agenda en https://www.biernet.nl/bier/aanbiedingen om dit probleem op " \
                            "te lossen. "
            message += extra_message
        # Send random message
        self.send_message(message, telegram_id)
        return

    def handle_command(self, chat, text, telegram_id):
        switcher = {
            '/help': self.show_help,
            '/info': self.show_info,
            '/nick': self.set_nick,
            '/nicks': self.show_nicks,
            '/products': self.show_products,
            '/debtors': self.show_debtors,
            '/all_tallies': self.show_all_tallies,
            '/tallies': self.show_tallies,
            '/add': self.add_product,
            '/all_history': self.show_all_history,
            '/history': self.show_history,
            '/thanks': self.thank_user,
            '/update': self.update_tally
        }
        split_text = text.split()
        command = split_text[0].split("@")[0]
        fun = switcher.get(command, self.command_not_found)
        fun(chat, split_text, telegram_id)
        return

    def command_not_found(self, chat, split_text, telegram_id):
        self.send_message("Command not found: " + split_text[0], chat)

    def show_help(self, chat, split_text, telegram_id):
        self.send_message(self.help_text, telegram_id)
        self.send_message(
            "Message answered privately. \nIf you didn't get my message, send me a private message and try again."
            , chat)

    def show_info(self, chat, split_text, telegram_id):
        self.send_message(self.info_text, telegram_id)
        self.send_message(
            "Message answered privately. \nIf you didn't get my message, send me a private message and try again."
            , chat)

    def set_nick(self, chat, split_text, telegram_id):
        if len(split_text) < 2:
            self.send_message("Provide new nick", chat)
            return
        if len(split_text[1]) > 12:
            self.send_message("Nick too long", chat)
            return
        if len(split_text[1]) < 2:
            self.send_message("Nick too short", chat)
            return
        user = self.db.get_user_by_telegram_id(telegram_id)
        old_nick = user.name
        user.name = split_text[1]
        self.db.add_user(user)
        self.send_message("Nick changed from " + old_nick + " to " + user.name, chat)

    def show_nicks(self, chat, split_text, telegram_id):
        users = self.db.get_all_users(chat)
        message = "=== NICKS === \n"
        for user in users:
            message += str(user.telegram_id) + ": " + user.name + "\n"
        self.send_message(message, chat)

    def show_products(self, chat, split_text, telegram_id):
        products = self.db.get_all_products(chat)
        message = "=== PRODUCTS ===\n"
        for product in products:
            message += product.name + "\n"
        self.send_message(message, chat)

    def show_debtors(self, chat, split_text, telegram_id):
        users = self.db.get_all_users(chat)
        message = "=== DEBTORS ===\n"
        for user in users:
            shown_name = False
            totals = self.db.get_all_tallies(chat, user)
            for key, value in totals.items():
                if value > 0:
                    if not shown_name:
                        message += user.name + ":\n"
                        shown_name = True
                    message += key + ": " + str(value) + "\n"
            if shown_name:
                message += "\n"
        self.send_message(message, chat)

    def show_all_tallies(self, chat, split_text, telegram_id):
        users = self.db.get_all_users(chat)
        message = "=== All tallies ===\n"
        for user in users:
            shown_name = False
            totals = self.db.get_all_tallies(chat, user)
            for key, value in totals.items():
                if value != 0:
                    if not shown_name:
                        message += user.name + ":\n"
                        shown_name = True
                    message += key + ": " + str(value) + "\n"
            if shown_name:
                message += "\n"
        message += "Total:\n"
        allTallies = self.db.get_total_tallies(chat)
        for key, value in allTallies.items():
            message += key + ": " + str(value) + "\n"
        self.send_message(message, chat)

    def show_tallies(self, chat, split_text, telegram_id):
        message = "=== Tallies ===\n"
        user = self.db.get_user_by_telegram_id(telegram_id)
        totals = self.db.get_all_tallies(chat, user)
        for key, value in totals.items():
            message += key + ": " + str(value) + "\n"
        self.send_message(message, telegram_id)
        self.send_message(
            "Message answered privately. \nIf you didn't get my message, send me a private message and try again."
            , chat)

    def add_product(self, chat, split_text, telegram_id):
        if telegram_id != self.ADMIN:
            self.send_message("🖕🖕🖕🖕🖕🖕🖕🖕🖕🖕🖕🖕🖕erw", chat)
            return
        self.db.add_product(Product(split_text[1], self.db.get_chat(chat)))
        self.show_products(chat, split_text, telegram_id)
        return

    def show_all_history(self, chat, split_text, telegram_id):
        if len(split_text) > 1:
            try:
                amount = int(split_text[1])
            except ValueError:
                self.send_message("Enter integer amount smaller than 99, " + str(split_text[1]) + " given.", chat)
                return
        else:
            amount = 10
        purchases = self.db.get_last_purchases(chat, amount)
        message = "=== All history ===\n"
        for purchase in purchases:
            message += "(" + parse(purchase.date).strftime("%m/%d %H:%M") + ") " + str(purchase.amount) + " " + \
                       purchase.product.name + " by " + purchase.user.name + "\n"
        self.send_message(message, chat)

    def show_history(self, chat, split_text, telegram_id):
        if len(split_text) > 1:
            try:
                amount = int(split_text[1])
            except ValueError:
                self.send_message("Enter integer amount, " + split_text[1] + " given.", chat)
                return
        else:
            amount = 10
        user = self.db.get_user_by_telegram_id(telegram_id)
        if not user:
            self.send_message("User not found", chat)
            return
        purchases = self.db.get_last_purchases(chat, amount, user)
        message = "=== History ===\n"
        for purchase in purchases:
            message += "(" + parse(purchase.date).strftime("%m/%d %H:%M") + ") " + str(purchase.amount) + " " + \
                       purchase.product.name + " by " + purchase.user.name + "\n"
        self.send_message(message, telegram_id)
        self.send_message(
            "Message answered privately. \nIf you didn't get my message, send me a private message and try again."
            , chat)

    def thank_user(self, chat, split_text, telegram_id):
        if len(split_text) < 2:
            self.send_message("No receiver given", chat)
            return
        receiver = self.db.get_user_by_name(chat, split_text[1])
        if receiver == False:
            self.send_message("Unknown user: " + split_text[1], chat)
            return
        user = self.db.get_user_by_telegram_id(telegram_id)
        group = self.db.get_chat(chat)
        self.db.add_purchase(Purchase(user, group.products[0], 1, self.db.get_chat(chat)))
        self.db.add_purchase(Purchase(receiver, group.products[0], -1, self.db.get_chat(chat)))
        message = "Thanks " + receiver.name + "! \nI don't know what you did " + receiver.name + ", but " + user.name + \
                  " would like to thank you! \n" + user.name + \
                  " has granted you a tally from his/her own pocket \nEnjoy, Tally"
        self.send_message(message, chat)

    def update_tally(self, chat, split_text, telegram_id):
        if telegram_id != self.ADMIN:
            self.send_message("🖕🖕🖕🖕🖕🖕", chat)
            return
        f = open(os.path.dirname(os.path.abspath(__file__)) + "/" + "update_tally", "w+")
        self.send_message("I will update shortly..", chat)
        f.close()

    def test(self):
        jsonFile = Path('post.json')
        if jsonFile.is_file():
            with open('post.json', 'r') as f:
                data = f.read().replace('\n', '')
                for tallyPost in self.decode_stacked(data):
                    x = tallyPost["amount"] + " " + tallyPost["product"]
                    self.handle_message(tallyPost["group"], x, tallyPost["user"], "", 'group')
                f.close()
            os.remove('post.json')


if __name__ == '__main__':
    tally = RadixEnschedeBot()
    if sys.argv[1] == "test":
        tally.test()

        exit()
    daemon_runner = runner.DaemonRunner(tally)
    daemon_runner.do_action()
