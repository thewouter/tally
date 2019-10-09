# @author Wouter van Harten <wouter@woutervanharten.nl>
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from Group import Group
from Purchase import Purchase
from base import Base


class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String)
    telegram_id = Column(Integer)
    purchases = relationship("Purchase", order_by=Purchase.id, back_populates="user")
    groups = relationship("Group", order_by=Group.id, back_populates="user")

    def __repr__(self):
        return "<User(name='%s, telegram_id='%s)>" % (self.name, self.telegram_id)

    def __init__(self, name, telegram_id):
        self.name = name
        self.telegram_id = telegram_id

    def set_name(self, name):
        self.name = name

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
