# @author Wouter van Harten <wouter@woutervanharten.nl>

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker

from Group import Group
from Product import Product
from Purchase import Purchase
from User import User
from base import Base


class DBHelper:
    session = None
    engine = None

    def __init__(self, dbname="tally.sqlite"):
        self.engine = create_engine('sqlite:///' + dbname, echo=False)
        sessionFactory = sessionmaker(bind=self.engine)
        self.session = sessionFactory()
        Base.metadata.create_all(self.engine)

    def get_chat(self, chat):
        return self.session.query(Group).filter_by(telegram_id=chat).first()

    def add_chat(self, chat):
        self.session.add(Group(telegram_id=chat))
        self.session.commit()

    def check_chat(self, chat):
        return self.get_chat(chat) is not None

    def get_user_by_telegram_id(self, telegram_id):
        user = self.session.query(User).filter_by(telegram_id=telegram_id).first()
        if user is not None:
            return user
        return False

    def get_user_by_name(self, chat, name):
        user = self.session.query(User).filter_by(name=name).filter(User.groups.any(telegram_id=chat)).first()
        if user is not None:
            return user
        return False

    def get_all_users(self, chat):
        return self.session.query(User).filter(User.groups.any(telegram_id=chat)).all()

    def get_user(self, user_id):
        return self.session.query(User).filter_by(id=user_id).first()

    def add_user(self, user):
        self.session.add(user)
        self.session.commit()

    def get_all_products(self, chat):
        return self.get_chat(chat).products

    def get_product(self, product_id,):
        return self.session.query(Product).filter_by(id=product_id).first()

    def add_product(self, product):
        self.session.add(product)
        self.session.commit()

    def get_product_by_name(self, chat, name):
        return self.session.query(Product).filter_by(name=name, group=self.get_chat(chat)).first()

    def get_last_purchases(self, chat, amount=10, user=None):
        if user is None:
            return self.session.query(Purchase)\
                .filter_by(group=self.get_chat(chat))\
                .order_by(Purchase.date.desc()) \
                .limit(amount)\
                .all()
        else:
            return self.session.query(Purchase) \
                .filter_by(group=self.get_chat(chat), user_id=user.id) \
                .order_by(Purchase.date.desc()) \
                .limit(amount) \
                .all()

    def get_purchase(self, purchase_id):
        return self.session.query(Purchase).filter_by(id=purchase_id).first()

    def add_purchase(self, purchase):
        self.session.add(purchase)
        self.session.commit()

    def get_all_tallies(self, chat, user):
        result = {}
        res = self.session.query(Purchase.product_id, func.sum(Purchase.amount))\
            .filter_by(user=user)\
            .filter_by(group=self.get_chat(chat))\
            .group_by(Purchase.product_id)\
            .order_by(Purchase.product_id.desc())\
            .all()
        for tup in res:
            result[self.get_product(tup[0]).name] = tup[1]
        return result

    def get_total_tallies(self, chat):
        result = {}
        res = self.session.query(Purchase.product_id, func.sum(Purchase.amount)) \
            .filter_by(group=self.get_chat(chat)) \
            .group_by(Purchase.product_id) \
            .order_by(Purchase.product_id.desc()) \
            .all()
        for tup in res:
            result[self.get_product(tup[0]).name] = tup[1]
        return result
