from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, Email, Length

class UserAddForm(FlaskForm):
    '''Form for adding users'''

    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[Length(min=8)])

class LoginForm(FlaskForm):
    '''Form for logging in user'''

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=8)])

class CocktailForm(FlaskForm):
    '''Form for choosing cocktail to make'''

    cocktail = StringField('Cocktail')
    ingredients = StringField('Ingredient')
