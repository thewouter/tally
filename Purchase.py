# @author Wouter van Harten <wouter@woutervanharten.nl>
import datetime

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from base import Base


class Purchase(Base):
    __tablename__ = 'purchases'
    id = Column(Integer, primary_key=True)
    amount = Column(Integer)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    group_id = Column(Integer, ForeignKey('groups.id'), nullable=False)
    date = Column(String)

    group = relationship("Group", back_populates="purchases")
    user = relationship("User", back_populates="purchases")
    product = relationship("Product", back_populates="purchases")

    def __repr__(self):
        return "<Purchase(amount='%s', product='%s', user='%s')>" % (str(self.amount), str(self.product), str(self.user))

    def __init__(self, user, product, amount, group, date=None):
        self.amount = amount
        self.product = product
        self.user = user
        self.group = group
        if date is None:
            date = str(datetime.datetime.now())
        self.date = date

    def set_id(self, id):
        self.id = id
