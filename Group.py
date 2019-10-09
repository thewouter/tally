# @author Wouter van Harten <wouter@woutervanharten.nl>
from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship

from base import Base


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)

    user = relationship('User', back_populates="groups")

    def __init__(self, id):
        self.id = id

    def __repr__(self):
        return "<Group(id='%s)>" % str(self.id)

    def get_id(self):
        return self.id

    def set_id(self, id):
        self.id = id
