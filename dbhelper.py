import sqlite3

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Product import Product
from Purchase import Purchase
from User import User
# @author Wouter van Harten <wouter@woutervanharten.nl>
from base import Base


class DBHelper:
    save_location = "/data/RadixEnschedeBot/"
    
    def __init__(self, dbname="tally.sqlite"):

        engine = create_engine('sqlite:///' + dbname, echo=True)

        sessionFactory = sessionmaker(bind=engine)
        session = sessionFactory()

        print(User.__table__.__repr__())

        Base.metadata.create_all(engine)

        session.commit()

        self.dbname = self.save_location + dbname
        self.conn = sqlite3.connect(dbname)
        stmt = "CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY)"
        self.conn.execute(stmt)

    def get_save_location(self):
        return self.save_location

    def add_chat(self, chat):
        dbname = self.save_location + "tally.sqlite"
        conn = sqlite3.connect(dbname)
        conn.execute("INSERT INTO chats(id) VALUES (" + str(chat) + ")")
        conn.commit()

    def check_chat(self, chat):
        dbname = self.save_location + "tally.sqlite"
        conn = sqlite3.connect(dbname)
        a = conn.execute("SELECT id FROM chats WHERE id = '" + str(chat) + "';")
        return len([x for x in a]) > 0

    def setup(self, chat):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt1 = "CREATE TABLE IF NOT EXISTS user (id INTEGER PRIMARY KEY, name text NOT NULL, " \
                "telegram_id text NOT NULL);"
        stmt2 = "CREATE TABLE IF NOT EXISTS product (id INTEGER PRIMARY KEY, name text NOT NULL);"
        stmt3 = "CREATE TABLE IF NOT EXISTS purchase (id INTEGER PRIMARY KEY, user INTEGER NOT NULL, " \
                "product INTEGER NOT NULL, amount INTEGER NOT NULL, chat INTEGER NOT NULL, date text)"
        conn.execute(stmt1)
        conn.execute(stmt2)
        conn.execute(stmt3)
        conn.commit()

    def get_user_by_telegram_id(self, chat, telegram_id):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT id FROM user WHERE telegram_id = (?)"
        result = [x for x in conn.execute(stmt, (str(telegram_id),))]
        if result != []:
            result = result[0][0]
            return self.get_user(chat, result)
        else:
            return False

    def get_user_by_name(self, chat, name):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT id FROM user WHERE name = (?)"
        result = [x for x in conn.execute(stmt, (str(name),))]
        if result != []:
            result = result[0][0]
            return self.get_user(chat, result)
        else:
            return False

    def get_all_users(self, chat, recursive=True):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT id FROM user"
        result = [x for x in conn.execute(stmt)]
        users = []
        for u in result:
            users.append(self.get_user(chat, u[0], recursive))
        return users

    def get_user(self, chat, user_id, recursive=True):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT * FROM user WHERE id = (?)"
        result = [x for x in conn.execute(stmt, (str(user_id),))]
        user = User(result[0][1], result[0][2])
        user.set_id(result[0][0])
        if recursive:
            stmt = "SELECT id FROM purchase WHERE user = (?)"
            result = [x for x in conn.execute(stmt, (str(user.id),))]
            purchases = []
            for purchase_id in result:
                purchases.append(self.get_purchase(chat, purchase_id[0], user, None))
            user.set_purchases(purchases)
        return user

    def save_user(self, chat, user):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        if user.id:
            number = [x for x in conn.execute("SELECT COUNT(id) FROM user WHERE id = " + str(user.id))]
        else:
            number = False
        if number != False:
            stmt = "UPDATE user SET name = '" + user.name + "', telegram_id = '" + str(user.telegram_id) + "' WHERE id = " + str(user.id)
        else:
            stmt = "INSERT INTO user(name, telegram_id) VALUES ('" + user.name + "','" + str(user.telegram_id) + "')"
        conn.execute(stmt)
        conn.commit()

    def get_all_products(self, chat, recursive=True):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT id FROM product"
        result = [x for x in conn.execute(stmt)]
        products = []
        for p in result:
            products.append(self.get_product(chat, p[0], recursive))
        return products

    def get_product(self, chat, product_id, recursive=True):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT * FROM product WHERE id = (?)"
        result = [x for x in conn.execute(stmt, (str(product_id),))]
        product = Product(result[0][1])
        product.set_id(result[0][0])
        if recursive:
            stmt = "SELECT id FROM purchase WHERE product = (?)"
            result = [x for x in conn.execute(stmt, (str(product.id),))]
            purchases = []
            for purchase_id in result:
                purchases.append(self.get_purchase(chat, purchase_id[0], None, product))
            product.set_purchases(purchases)
        return product

    def save_product(self, chat, product):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        if product.id:
            number = [x for x in conn.execute("SELECT COUNT(id) FROM product WHERE id = " + str(product.id))]
        else:
            number = False
        if number != False:
            stmt = "UPDATE product SET name = '" + product.name + "' WHERE id = " + str(product.id)
        else:
            stmt = "INSERT INTO product(name) VALUES ('" + product.name + "')"
        conn.execute(stmt)
        conn.commit()

    def get_product_by_name(self, chat, name):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT id FROM product WHERE name = (?)"
        result = [x for x in conn.execute(stmt, (str(name),))]
        if result != []:
            result = result[0][0]
            return self.get_product(chat, result)
        else:
            return False

    def get_last_purchases(self, chat, amount, user=None):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        if user is None:
            stmt = "SELECT id FROM purchase WHERE chat = '" + str(chat) + "' ORDER BY date DESC LIMIT " + str(amount) + ""
        else:
            stmt = "SELECT id FROM purchase WHERE user = " + str(user.id) + " AND chat = '" + str(chat) +\
                   "' ORDER BY date DESC LIMIT " + str(amount)
        result = [x for x in conn.execute(stmt)]
        purchases = []
        for p in result:
            purchases.insert(0, self.get_purchase(chat, p[0]))
        return purchases

    def get_purchase(self, chat, purchase_id, user=None, product=None):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT * FROM purchase WHERE id = (?)"
        result = [x for x in conn.execute(stmt, (str(purchase_id),))]
        if user is None:
            user = self.get_user(chat, result[0][1], False)
        if product is None:
            product = self.get_product(chat, result[0][2], False)
        purchase = Purchase(user, product, result[0][3], result[0][4], result[0][5])
        purchase.set_id(result[0][0])
        return purchase

    def save_purchase(self, chat, purchase):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        if purchase.id:
            number = [x for x in conn.execute("SELECT COUNT(id) FROM purchase WHERE id = " + str(purchase.id))]
        else:
            number = False
        if number != False:
            stmt = "UPDATE purchase SET product = '" + str(purchase.product.id) + "', chat = '" + str(purchase.chat) + \
                   "', user = '" + str(purchase.user.id) + "', date = '" + purchase.date + "'  WHERE id = " + str(purchase.id)
        else:
            stmt = "INSERT INTO purchase (product, chat, user, amount, date) VALUES ('" + str(purchase.product.id) + "', '" + \
               str(purchase.chat) + "', '" + str(purchase.user.id) + "','" + str(purchase.amount) + "', '" + purchase.date + "')"
        conn.execute(stmt)
        conn.commit()

    def get_all_tallies(self, chat, user):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT product, SUM(amount) FROM purchase WHERE user=" + str(user.id) + " GROUP BY product ORDER BY product DESC"
        quer = [x for x in conn.execute(stmt)]
        result = {}
        for tup in quer:
            result[self.get_product(chat, tup[0], False).name] = tup[1]
        return result

    def get_total_tallies(self, chat):
        dbname = self.save_location + str(chat) + ".sqlite"
        conn = sqlite3.connect(dbname)
        stmt = "SELECT product, SUM(amount) FROM purchase GROUP BY product ORDER BY product DESC"
        quer = [x for x in conn.execute(stmt)]
        result = {}
        for tup in quer:
            result[self.get_product(chat, tup[0], False).name] = tup[1]
        return result
