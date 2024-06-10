from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True,)
    username = db.Column(db.String, nullable=False, unique=True,)
    password = db.Column(db.String,nullable=False,)
    drinkposts = db.relationship('DrinkPost', back_populates='user', lazy=True)
# backref='creator'

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"


    @classmethod
    def signup(cls, username, password):
        """Sign up user.
        """


        user = User(
            username=username,
            password=password,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = (user.password, password)
            if is_auth:
                return user

        return False



class Drink(db.Model):
    '''Drink'''

    __tablename__ = 'drinks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    api_id = db.Column(db.Integer, unique=True)
    name = db.Column(db.String, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    category = db.relationship('Category', backref=db.backref('drinks', lazy=True))
    instructions = db.Column(db.String, )
    image = db.Column(db.String)
    category = db.relationship('Category', backref='drinks')

''' Ingredients class '''
class Ingredient(db.Model):

    __tablename__ = 'ingredients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True)
    description = db.Column(db.String)
    abv = db.Column(db.String, default='Non-Alcoholic')


class Category(db.Model):

    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String, unique=True, nullable=False)

class DrinkIngredient(db.Model):

    __tablename__ = 'drink_ingredients'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.id', ondelete='CASCADE'))
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id', ondelete='CASCADE'))
    measurement = db.Column(db.String, default='Personal preference')
    drink = db.relationship('Drink', backref='ingredients')
    ingredient = db.relationship('Ingredient', backref='drinks')


class Favorite(db.Model):

    __tablename__ = 'favorites'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.id', ondelete='CASCADE'))
    user = db.relationship('User', backref='favorites')
    drink = db.relationship('Drink', backref='favorites')


class DrinkPost(db.Model):

    __tablename__ = 'drinkposts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'))
    drink_id = db.Column(db.Integer, db.ForeignKey('drinks.id'))
    user = db.relationship('User', back_populates='drinkposts')
    drink = db.relationship('Drink', backref='user')


def connect_db(app):
    db.app = app
    db.init_app(app)