# @author Wouter van Harten <wouter@woutervanharten.nl>

class Product(object):
    id = None
    name = None
    purchases = []

    def __init__(self, name):
        self.name = name

    def set_purchases(self, purchases):
        self.purchases = purchases

    def set_id(self, id):
        self.id = id

    def get_total_per_user(self, chat):
        totals = {}
        keys = []
        for purchase in self.purchases:
            if purchase.chat == chat:
                if purchase.product.id in keys:
                    totals[purchase.user.name] += purchase.amount
                else:
                    totals[purchase.user.name] = purchase.amount
                    keys.append(purchase.id)
        return totals
