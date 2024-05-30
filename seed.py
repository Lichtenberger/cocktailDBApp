from csv import DictReader
from app import db
from models import Cocktails, User

db.drop_all()
db.create_all()

with open('generator/user.csv') as users:
    db.session.bulk_insert_mappings(User, DictReader(users))

with open('generator/cocktail.csv') as cocktails:
    db.session.bulk_insert_mappings(Cocktails, DictReader(cocktails))

db.session.commit()