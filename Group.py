# @author Wouter van Harten <wouter@woutervanharten.nl>
from sqlalchemy import Column, Integer, ForeignKey, Table
from sqlalchemy.orm import relationship

from base import Base, association_table


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)

    users = relationship('User', secondary=association_table, back_populates="groups")
    products = relationship('Product', back_populates="group")
    purchases = relationship('Purchase', back_populates="group")

    def __init__(self, telegram_id):
        self.telegram_id = telegram_id

    def __repr__(self):
        return "<Group(id='%s)>" % str(self.id)

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id