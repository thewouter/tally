import sqlite3

from Product import Product
from Purchase import Purchase
from User import User
from base import Base
from dbhelper import DBHelper

def create_connection(db_file):
    """ create a database connection to the SQLite database
        specified by the db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except sqlite3.Error as e:
        print(e)

    return conn


db = DBHelper()

con = create_connection('radix.sqlite')

purchases = con.execute("SELECT * FROM purchase").fetchall()

group = db.get_chat(-1001487022745)

for tup in purchases:
    u = db.get_user(tup[1])
    pr = db.get_product(tup[2])
    amount = tup[3]
    p = Purchase(u, pr, amount, group, date=tup[5])
    db.add_purchase(p)







