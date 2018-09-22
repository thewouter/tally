# @author Wouter van Harten <wouter@woutervanharten.nl>

class User(object):
    id = None
    name = None
    telegram_id = None
    purchases = []

    def __init__(self, name, telegram_id):
        self.name = name
        self.telegram_id = telegram_id

    def set_purchases(self, purchases):
        self.purchases = purchases

    def set_id(self, id):
        self.id = id

    def get_total_per_product(self, chat):
        totals = {}
        keys = []
        for purchase in self.purchases:
            if purchase.chat == chat:
                if purchase.product.id in keys:
                    totals[purchase.product.name] += purchase.amount
                else:
                    totals[purchase.product.name] = purchase.amount
                    keys.append(purchase.product.id)
        return totals

    def get_purchases(self):
        return self.purchases
