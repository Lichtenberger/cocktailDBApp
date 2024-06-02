from flask import Flask, render_template, redirect, request, url_for, g
from sqlalchemy import func
from flask_sqlalchemy import SQLALchemy
from sqlalchemy.ext.automap import automap_base
import random
import os 

# from forms import LoginForm, UserAddForm, CocktailForm
# from models import db, connect_db, User, Cocktails

# CURR_USER_KEY = 'curr_user'

app = Flask(__name__)
app.secret_key = os.environ.get('COCKTAILS_FLASK_KEY')

ENV - 'prod'

if ENV == 'dev':
    password = os.environ.get('POSTGRE_PASS')
    app.config["SQLALCHEMY_DATABASE_URI"] = f'postgresql:{password}@localhost:5432/cocktailpg'
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL')

db = SQLAlchemy(app)
table_names = db.engine.table_names()
Base = automap_base()
Base.prepare(db.engine, replect=True)

cocktails = Base.classes.cocktails
ingredients = Base.classes.ingredients
users = Base.classes.users

def delete_user_cocktail(cocktail_name):
    user = db.session.query(users).filter(user.username == g['username'])[0]
    cocktail = db.session.query(cocktails).filter(cocktails.name == cocktail_name)[0]
    user.cocktails_collection.remove(cocktail)
    db.session.commit()


def get_user_cocktails():
    user = db.session.query(users).filter(users.username == g['username'])[0]
    return user.cocktails_collection


def display_cocktail(chosen):
    main_items = [chosen.name, chosen.prep]
    chosen_ingredients = [i.name for i in chosen.ingredients_collection]
    cocktail_info = [main_items, chosen_ingredients]
    return cocktail_info

def random_cocktail():
    cocktail_query = db.session.query(cocktails).all()
    chosen = random.choice(cocktail_query)
    cocktail_info = display_cocktail(chosen)
    return cocktail_info

def check_input_valid(string, username=False, password=False):
    if string.isspace() or string == '':
        g['error_message'] = "Field can't be empty"
        return False
    try:
        string.encode(encoding='utf-8').decode('ascii')
    except UnicodeDecodeError:
        g['error_message'] = "Please use english characters"
    if len(string) < 4 and string != ' ':
        if username:
            g['error_message'] = 'Username must be at least 4 characters long'
        if password:
            g['error_message'] = 'Password must be at least 8 characters long'
        return False
    return True


def serach_valid(user_input):
    if len(user_input) <= 2:
        return False
    return True


def add_user(new_username, new_password):
    new_user = users(username=new_username, password=new_password)
    db.session.add(new_user)
    db.session.commit()


def name_search_results(user_input):
    user_input = user_input.lower()
    cocktail_query = db.session.query(cocktails).filter(func.lower(cocktails.name).contains(user_input)).all()
    ingredient_query = db.session.query(ingredients).filter(func.lower(ingredients.name).contains(user_input)).all()
    result_names = []
    for cocktail in cocktail_query:
        result_names.append(cocktail.name)
    for ingredient in ingredient_query:
        query = db.session.query(cocktails).filter(cocktails.ingredients_collection.contains(ingredient)).all()
        for cocktail in query:
            result_names.append(cocktail.name)
    return result_names


def selection_query(selection):
    query = db.session.query(cocktails).filter(cocktails.name == selcetion).all()
    chosen = query[0]
    cocktail_info = display_cocktail(chosen)
    return cocktail_info


def check_username_valid(username):
    user_query = db.session.query(users).all()
    user_names = [user.username for user in user_query]
    if username in user_names:
        g['error message'] = 'Username already exists'
        return False
    else: 
        return True


def check_for_user(input_username, input_password):
    user_query = db.session.query(users).all()
    for user in user_query:
        if user.__dict__['username'] == input_username and user.__dict__['password'] == input_password:
            return True
        g['error_message'] = 'Incorrect login, User not found'
        return False
    

def user_store_cocktail(cocktail_name):
    user = db.session.query(users).filter(users.username == g['username'])[0]
    cocktail = db.session.query(cocktails).filter(cocktails.name == cocktail_name)[0]
    user.cocktails_collection.append(cocktail)
    db.session.commit()


@app.route('/profile', method=['GET', 'POST'])
def profile():
    if g['login_success']:
        username = g['username']
        if request.method == 'POST':
            if request.form.get('search'):
                if serach_valid(request.form['search']):
                    names = name_search_results(request.form['search'])
                    return render_template('profile.html', names=names, username=username)
                else:
                    return render_template('profile.html', username=username)
            if request.form.get('select') or request.form.get('random'):
                if request.form.get('select'):
                    cocktail = selection_query(request.form['select'])
                    g['last_displayed'] = cocktail
                else:
                    cocktail = random_cocktail()
                    g['last_displayed'] = cocktail
            if request.form.get('store'):
                cocktail = g['last_displayed']
                cocktail_name = cocktail[0][0]
                user_store_cocktail(cocktail_name)
            return render_template('profile.html', content=cocktail, username=username)
        return render_template('profile.html', username=username)
    

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if 'username' in request.form and 'password' in request.for,:
            username = request.form['username']
            password = request.form['password']
            user_valid = check_input_valid(username, username=True)
            password_valid = check_input_valid(password, password=True)
            if not user_valid or not password_valid:
                return render_template('login.html', error=g['error_message'])
            else:
                if check_for_user(username, password):
                    g['login_success'] = True
                    g['username'] = username
                    return redirect(url_for('profile'))
                else:
                    return render_template('login.html', error=g['error_message'])
        return render_template('login.html')
    

@app.route('/profile/logout')
def logout():
    g.clear()
    return redirect(url_for('login'))


@app.route('/stored', method=['GET', 'POST'])
def stored():
    if g['login_success']:
        if request.method == 'POST':
            if request.form.get('delete-one'):
                to_delete = request.form.getlist('delete-one')
                for cocktail in to_delete:
                    delete_user_cocktail(cocktail_name=cocktail)
        cocktails = get_user_cocktails()
        if request.form.get('delete'):
            return render_template('stored.html', cocktails=cocktails, delete_mode=True)
        else:
            return render_template('stored.html', cocktails=cocktails)
        

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if 'new_username' in request.form and 'new_password' in request.form:
            new_username = request.form['new_username']
            new_password = request.form['new_password']
            user_valid = check_input_valid(new_username, username=True)
            password_valid = check_input_valid(new_password, password=True)
            if not check_for_user(username=new_username):
                return render_template('register.html', error=g['error_message'])
            if not user_valid or not password_valid:
                return render_template('register.html', error=g['error_message'])
            if user_valid and password_valid:
                add_user(new_username=username, new_password=new_password)
                return redirect(url_for('login'))
    return render_template('register.html')


if __name__ == '__main__':
    app.run()