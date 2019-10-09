from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Product import Product
from Purchase import Purchase
from User import User
from base import Base

engine = create_engine('sqlite:///database.sqlite', echo=True)
sessionFactory = sessionmaker(bind=engine)
session = sessionFactory()

print(User.__table__.__repr__())

Base.metadata.create_all(engine)

product = Product("prod1")
user = User("naam", 1)
q_user = session.query(User).filter_by(name='naam').first()
print(user is q_user)
session.add(product)
user.set_name("othername")

purchase = Purchase(user, product, 49, 1)
session.commit()
