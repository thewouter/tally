from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

association_table = Table('association', Base.metadata,
                          Column('group_id', Integer, ForeignKey('groups.id')),
                          Column('user_id', Integer, ForeignKey('users.id')))
