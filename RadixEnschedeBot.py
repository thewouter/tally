# @author Wouter van Harten <wouter@woutervanharten.nl>

import json
import requests
import urllib
import random

from dbhelper import DBHelper
from user import User
from purchase import Purchase
from product import Product
from NumericStringParser import NumericStringParser
from pprint import pprint
from dateutil.parser import parse

db = DBHelper()

TOKEN = "520500213:AAGkIMSBHc69uaC8SjfVlov2FQ6Saxt3rO0"
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
ADMIN = 510984003

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

info_text = """Tally is a simple Telegram-bot
He is created because someone was to lazy to stand up and tally his beer. 
This someone rather preferred program a complete Telegram-bot.
You're free to use Tally for your own purposes, however Tally is confronted with alcoholic beverages on a regular basis. 
Therefore Tally, nor it's maker can guarantee that Tally is and will stay functioning at a socially acceptable level. 
Honestly, we wouldn't be surprised if Tally would get Korsakoff, or have some troubles with (temporary) black-outs. Let alone that he stays alive.

- Wouter (tally@woutervanharten.nl)"""

def get_url(url):
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content


def get_json_from_url(url):
    content = get_url(url)
    js = json.loads(content)
    return js


def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset)
    js = get_json_from_url(url)
    return js


def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)


def get_last_update_id(updates):
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)


def send_message(text, chat_id, reply_markup=None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)


def test2():
    db.setup(-294368505)
    db.save_user(-294368505, User("a", 1))
    db.save_user(-294368505, User("b", 2))
    db.save_user(-294368505, User("c", 3))
    db.save_user(-294368505, User("d", 4))
    db.save_user(-294368505, User("e", 5))
    db.save_user(-294368505, User("f", 6))
    db.save_product(-294368505, Product("aa"))
    db.save_product(-294368505, Product("bb"))
    db.save_product(-294368505, Product("cc"))
    u1 = db.get_user_by_name(-294368505, "a")
    u2 = db.get_user_by_name(-294368505, "b")
    u3 = db.get_user_by_name(-294368505, "c")
    u4 = db.get_user_by_name(-294368505, "d")
    u5 = db.get_user_by_name(-294368505, "e")
    u6 = db.get_user_by_name(-294368505, "f")
    u = [u1, u2, u3, u4, u5, u6]
    p1 = db.get_product_by_name(-294368505, "aa")
    p2 = db.get_product_by_name(-294368505, "bb")
    p3 = db.get_product_by_name(-294368505, "cc")
    p = [p1, p2, p3]
    for i in range(1, 10):
        db.save_purchase(-294368505, Purchase(random.choice(u), random.choice(p), random.randint(1, 9), -294368505))

    pprint(vars(db.get_user(-294368505, 1)))
    message = "=== Tallies ===\n"
    totals = db.get_user_by_telegram_id(-294368505, 2).get_total_per_product(-294368505)
    for key, value in totals.items():
        message += key + ": " + str(value) + "\n"
    print(message)
    return


def test():
    nsp = NumericStringParser()
    print(int(nsp.eval('7/2')))


def main():
    # test2()
    # return
    last_update_id = None
    while True:
        updates = get_updates(last_update_id)
        if len(updates["result"]) > 0:
            last_update_id = get_last_update_id(updates) + 1
            extract_messages(updates)


def extract_messages(updates):
    for update in updates["result"]:
        try:
            text = update["message"]["text"]
            chat = update["message"]["chat"]["id"]
            telegram_id = update["message"]["from"]["id"]
            name = update["message"]["from"]["first_name"]
            type = update["message"]["chat"]["type"]
            handle_message(chat, text, telegram_id, name, type)

        except Exception as e:
            print(e)
            print(update)
            print("")


def personal_message(chat, text, telegram_id, name):
    if str(telegram_id) != str(ADMIN):
        send_message("Add me to a group :)", telegram_id)
        return

    split_text = text.split()
    switcher = {
        '/add_chat': add_chat
    }
    fun = switcher.get(split_text[0], command_not_found)
    fun(chat, split_text, telegram_id)


def add_chat(chat, split_text, telegram_id):
    db.add_chat(int(split_text[1]))
    send_message("Added " + split_text[1], ADMIN)


def handle_message(chat, text, telegram_id, name, type):
    text = text.lower()

    # Check if in group
    if type != 'group':
        personal_message(chat, text, telegram_id, name)
        return
    # Check if chat allowed

    if not db.check_chat(chat):
        send_message("Ask Wouter van Harten (+31)6 833 24 277 to whitelist <" + str(chat) + ">", chat)
        send_message("Activity from unknown chat <" + str(chat) + ">, maybe you can whitelist it with '/add_chat " + str(chat) + "' ?", ADMIN)
        return

    # Build/Check chat database
    db.setup(chat)

    # Check for STFU
    if text[0] == ".":
        return
    # Check for command
    if text[0] == '/':
        handle_command(chat, text, telegram_id)
        return

    split_text = text.split()

    nsp = NumericStringParser()

    try:
        int(nsp.eval(split_text[0]))
        tally(split_text, chat, telegram_id, name)
        return
    except Exception:
        pass

    # Try for username
    user = db.get_user_by_name(chat, split_text[0])
    if user != False:
        del split_text[0]
        try:
            int(nsp.eval(split_text[0]))
            tally(split_text, chat, user.telegram_id, split_text[0], False)
            return
        except Exception:
            send_message("unknown amount: " + split_text[0], chat)
            pass
        return

    send_message("Que? (" + text + ")", chat)


def tally(split_text, chat, telegram_id, name, make_new_user=True):
    nsp = NumericStringParser()
    amount = int(nsp.eval(split_text[0]))
    if abs(amount) > 99:
        send_message("Tally between -100 and 100, " + str(amount) + " given", chat)
        return
    user = db.get_user_by_telegram_id(chat, telegram_id)
    if (not make_new_user) & (user == False):
        send_message("Unkown user: " + name, chat)
        return
    if user == False:
        user = User(name.lower(), telegram_id)
        db.save_user(chat, user)
    user = db.get_user_by_telegram_id(chat, telegram_id)
    if len(split_text) < 2:
        product = db.get_product(chat, 1)
    else:
        product = db.get_product_by_name(chat, split_text[1])
        if product == False:
            send_message("Unknown product: " + split_text[1], chat)
            return
    purchase = Purchase(user, product, amount, chat)
    # Get old score and new score
    all_tallies = db.get_all_tallies(chat, user)
    if product.name in all_tallies.keys():
        old_score = all_tallies[product.name]
        new_score = old_score + amount
    else:
        old_score = 0
        new_score = amount
    # If user remains on the right end, simple message:
    if new_score < 0:
        send_message("Tallied " + str(amount) + " " + product.name + " for " + user.name + " (current balance is " + new_score + " " + product + ").", chat)
    # If user remains on the wrong end with a positive tally, add a simple notification & a personal message:
    elif (old_score > 0) and (new_score > 0) and (amount > 0):
        send_message("Tallied " + str(amount) + " " + product.name + " for " + user.name + " (current balance is " + new_score + " " + product + ").\n" + user.name + " has run out of " + product.name + " and is consuming another person's " + product.name + "!", chat)
        send_message("Dear " + user.name + ", on this special occasion I would like to share with you a piece of wisdom our former queen shared with her son, the king:\n'Hee majesteit, ga eens bier halen!'", telegram_id)
    # If a user remains on the wrong end with a negative tally, a more encouraging message:
    elif (old_score > 0) and (new_score > 0) and (amount < 0):
        send_message("Tallied " + str(amount) + " " + product.name + " for " + user.name + " (current balance is " + new_score + " " + product + ").\n" + user.name + ", thank you for adding some " + product.name + " to your stock. You did not add enough to return to Tally's good graces, though!", chat)
    # Warn a user if their last item is tallied:
    elif (new_score > 0) and (old_score < 0):
        send_message("Tallied " + str(amount) + " " + product.name + " for " + user.name + " (current balance is " + new_score + " " + product + ").\n Better enjoy that " + product.name + ", " + user.name + "! You've depleted your stock!", chat)
        send_message(user.name + ", your last " + product.name + " was just tallied!", telegram_id)
    db.save_purchase(chat, purchase)


def handle_command(chat, text, telegram_id):
    switcher = {
        '/help': show_help,
        '/info': show_info,
        '/nick': set_nick,
        '/nicks': show_nicks,
        '/products': show_products,
        '/debtors': show_debtors,
        '/all_tallies': show_all_tallies,
        '/tallies': show_tallies,
        '/add': add_product,
        '/all_history': show_all_history,
        '/history': show_history,
        '/thanks': thank_user,
        '/update': update_tally
    }
    split_text = text.split()
    command = split_text[0].split("@")[0]
    fun = switcher.get(command, command_not_found)
    fun(chat, split_text, telegram_id)

    return


def command_not_found(chat, split_text, telegram_id):
    send_message("Command not found: " + split_text[0], chat)


def show_help(chat, split_text, telegram_id):
    send_message(help_text, telegram_id)
    send_message("Message answered privately. \nIf you didn't get my message, send me a private message and try again."
                 , chat)


def show_info(chat, split_text, telegram_id):
    send_message(info_text, telegram_id)
    send_message("Message answered privately. \nIf you didn't get my message, send me a private message and try again."
                 , chat)


def set_nick(chat, split_text, telegram_id):
    if len(split_text) < 2:
        send_message("Provide new nick", chat)
        return
    if len(split_text[1]) > 12:
        send_message("Nick to long", chat)
        return
    user = db.get_user_by_telegram_id(chat, telegram_id)
    old_nick = user.name
    user.name = split_text[1]
    db.save_user(chat, user)
    send_message("Nick changed from " + old_nick + " to " + user.name, chat)


def show_nicks(chat, split_text, telegram_id):
    users = db.get_all_users(chat)
    message = "=== NICKS === \n"
    for user in users:
        message += user.telegram_id + ": " + user.name + "\n"
    send_message(message, chat)


def show_products(chat, split_text, telegram_id):
    products = db.get_all_products(chat)
    message = "=== PRODUCTS ===\n"
    for product in products:
        message += product.name + "\n"
    send_message(message, chat)


def show_debtors(chat, split_text, telegram_id):
    users = db.get_all_users(chat, False)
    message = "=== DEBTORS ===\n"
    for user in users:
        shown_name = False
        totals = db.get_all_tallies(chat, user)
        for key, value in totals.items():
            if value > 0:
                if not shown_name:
                    message += user.name + ":\n"
                    shown_name = True
                message += key + ": " + str(value) + "\n"
        if shown_name:
            message += "\n"
    send_message(message, chat)


def show_all_tallies(chat, split_text, telegram_id):
    users = db.get_all_users(chat, False)
    message = "=== All tallies ===\n"
    for user in users:
        shown_name = False
        totals = db.get_all_tallies(chat, user)
        for key, value in totals.items():
            if value != 0:
                if not shown_name:
                    message += user.name + ":\n"
                    shown_name = True
                message += key + ": " + str(value) + "\n"
        if shown_name:
            message += "\n"
    message += "Total:\n"
    allTallies = db.get_total_tallies(chat)
    for key, value in allTallies.items():
        message += key + ": " + str(value) + "\n"
    send_message(message, chat)


def show_tallies(chat, split_text, telegram_id):
    message = "=== Tallies ===\n"
    totals = db.get_user_by_telegram_id(chat, telegram_id).get_total_per_product(chat)
    for key, value in totals.items():
        message += key + ": " + str(value) + "\n"
    send_message(message, telegram_id)
    send_message("Message answered privately. \nIf you didn't get my message, send me a private message and try again."
                 , chat)


def add_product(chat, split_text, telegram_id):
    if telegram_id != ADMIN:
        send_message("🖕🖕🖕🖕🖕🖕", chat)
        return
    db.save_product(chat, Product(split_text[1]))
    show_products(chat, split_text, telegram_id)
    return


def show_all_history(chat, split_text, telegram_id):
    if len(split_text) > 1:
        try:
            amount = int(split_text[1])
        except ValueError:
            send_message("Enter integer amount smaller than 99, " + str(split_text[1]) + " given.", chat)
            return
    else:
        amount = 10
    purchases = db.get_last_purchases(chat, amount)
    message = "=== All history ===\n"
    for purchase in purchases:
        message += "(" + parse(purchase.date).strftime("%m/%d %H:%M") + ") " + str(purchase.amount) + " " +\
                   purchase.product.name + " by " + purchase.user.name + "\n"
    send_message(message, chat)


def show_history(chat, split_text, telegram_id):
    if len(split_text) > 1:
        try:
            amount = int(split_text[1])
        except ValueError:
            send_message("Enter integer amount, " + split_text[1] + " given.")
            return
    else:
        amount = 10
    user = db.get_user_by_telegram_id(chat, telegram_id)
    if user == False:
        send_message("User not found", chat)
        return
    purchases = db.get_last_purchases(chat, amount, user)
    message = "=== History ===\n"
    for purchase in purchases:
        message += "(" + parse(purchase.date).strftime("%m/%d %H:%M") + ") " + str(purchase.amount) + " " +\
                   purchase.product.name + " by " + purchase.user.name + "\n"
    send_message(message, telegram_id)
    send_message("Message answered privately. \nIf you didn't get my message, send me a private message and try again."
                 , chat)


def thank_user(chat, split_text, telegram_id):
    if len(split_text) < 2:
        send_message("No receiver given", chat)
        return
    receiver = db.get_user_by_name(chat, split_text[1])
    if receiver == False:
        send_message("Unknown user: " + split_text[1], chat)
        return
    user = db.get_user_by_telegram_id(chat, telegram_id)
    db.save_purchase(chat, Purchase(user, db.get_product(chat, 1), 1, chat))
    db.save_purchase(chat, Purchase(receiver, db.get_product(chat, 1), -1, chat))
    message = "Thanks " + receiver.name + "! \nI don't know what you did " + receiver.name + ", but " + user.name + \
              " would like to thank you! \n" + user.name + \
              " has granted you a tally from his/her own pocket \nEnjoy, Tally"
    send_message(message, chat)


def update_tally(chat, split_text, telegram_id):
    if telegram_id != ADMIN:
        send_message("🖕🖕🖕🖕🖕🖕", chat)
        return
    f = open(db.get_save_location() + "update_tally", "w+")
    send_message("I will update shortly...", chat)
    f.close()


if __name__ == '__main__':
    main()
