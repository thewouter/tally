# @author Wouter van Harten <wouter@woutervanharten.nl>
import datetime

class Purchase(object):

    id = None
    amount = None
    product = None
    user = None
    date = None

    def __init__(self, user, product, amount, chat, date=None):
        self.amount = amount
        self.product = product
        self.user = user
        self.chat = chat
        if date is None:
            date = str(datetime.datetime.now())
        self.date = date

    def set_id(self, id):
        self.id = id
