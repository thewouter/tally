# @author Wouter van Harten <wouter@woutervanharten.nl>
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from Purchase import Purchase
from base import Base


class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String)
    group_id = Column(Integer,  ForeignKey('groups.id'))

    purchases = relationship("Purchase", order_by=Purchase.id, back_populates="product")
    group = relationship("Group", back_populates="products")

    def __init__(self, name, group):
        self.name = name
        self.group = group

    def __repr__(self):
        return "<Product(name='%s)>" % self.name

    def set_purchases(self, purchases):
        pass

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
