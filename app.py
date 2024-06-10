from flask import Flask, render_template, redirect, session, g, flash, url_for
from sqlalchemy.exc import IntegrityError
from jinja2 import Environment, select_autoescape
import random
import os 
import math
from models import connect_db, db, User, Drink, Ingredient, DrinkIngredient, Category, Favorite, DrinkPost
from forms import SignupForm, LoginForm, DrinkForm, SearchForm, IngredientsForm, EditDrinkIngredientForm

CURR_USER_KEY = "curr_user"

app = Flask(__name__)
app.app_context().push()

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'postgresql://localhost:5432/cocktailsdb')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', "it's a secret")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False


connect_db(app)

@app.context_processor
def inject_data():

    categories = Category.query.order_by(Category.name).all()
    search_form = SearchForm()
    return dict(categories=categories, DrinkPost=DrinkPost, search_form=search_form)


def inject_funcs():
    
    check_favorites = add_favorites_to_g()
    return dict(check_favorites=check_favorites, check_author=check_author, len=len, math=math)

    
def check_author(post):
    
    if g.user == post.user:
        return True
    else: 
        return False
    
app.jinja_env.globals.update(check_author=check_author)

@app.before_request   
def add_user_to_g():

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])
    else:
        g.user = None

def add_favorites_to_g():
    if 'curr_user' in session:
        g.user = User.query.get(session['curr_user'])
        g.favorites = [f.drink for f in g.user.favorites]
    else:
        g.user = None
        g.favorites = None

@app.before_request
def before_request():
    add_favorites_to_g()

def check_favorites(drink_id):
    if g.favorites:
        return drink_id in g.favorites
    else:
        return False

app.jinja_env.globals.update(check_favorites=check_favorites)
        

def sess_login(user):

    session[CURR_USER_KEY] = user.id

def sess_logout():

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]

def get_random_drink():
        count = 0
        drink_list = []

        while count < 3:
            drinks = Drink.query.all()
            idx = random.randint(0, len(drinks) - 1)
            drink_list.append(drinks[idx])
            count += 1

        return drink_list

def get_drinks_from_database():

    from models import Drink
    drinks = Drink.query.all()
    return drinks

@app.route("/")
def show_home():
    """Show homepage - if logged in showcase random drink"""

    drinks = get_drinks_from_database()
    if g.user and g.favorites:
        return render_template("home.html", drinks=drinks)
    elif g.user and not g.favorites: 
        drinks = get_random_drink()
        return render_template('home.html', drinks=drinks)
    else: 
        return render_template('home.html')


@app.route("/signup", methods=["GET", "POST"])
def signup_user():
    """Signup a new user via class method, save hashed password to database"""

    form = SignupForm()

    if form.validate_on_submit():
        
            try:
                user = User.signup(
                    username=form.username.data,
                    password=form.password.data,
                )
                db.session.commit()
                sess_login(user)

                flash(f"Welcome {user.username}!", "success")
                return redirect("/")
            except IntegrityError:
                db.session.rollback()
                flash("Sorry, that username is already taken!", "danger")
                return render_template("signup.html", form=form)
    else:
        return render_template("signup.html", form=form)


@app.route("/login", methods=["GET", "POST"])
def login_user():
    """Authenticate user via class method and login"""

    form = LoginForm()

    if form.validate_on_submit():
        try:
            user = User.authenticate(
                username=form.username.data, password=form.password.data
            )
            sess_login(user)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect("/")
        except:
            flash("Sorry, please try again!", "danger")
            return render_template("login.html", form=form)
    else:
        return render_template("login.html", form=form)


@app.route("/logout")
def logout_user():
    """Log a user out"""

    sess_logout()
    flash(f"{g.user.username} has now been logged out.", "warning")
    return redirect("/")


@app.route("/profile/<int:user_id>")
def show_user_profile(user_id):
    """Show user information"""

    user = User.query.get_or_404(user_id)
    favorites = []
    drinkposts = []

    for favs in user.favorites:
        fav_drink = Drink.query.get_or_404(favs.drink_id)
        favorites.append(fav_drink)

    for posts in user.drinkposts:
        drink = Drink.query.get_or_404(posts.drink_id)
        drinkposts.append(drink)

    return render_template(
        "profile.html", user=user, favorites=favorites, posts=drinkposts
    )


@app.route("/<int:drink_id>/favorite/add")
def add_favorite(drink_id):
    """Add user favorite to database"""

    if g.user:
        f = Favorite(user_id=g.user.id, drink_id=drink_id)

        db.session.add(f)
        db.session.commit()

        flash("Drink successfully added!", "success")
        return redirect(f"/{drink_id}")
    else:
        flash("You must be logged in to add favorites!", "warning")
        return redirect("/login")


@app.route("/<int:drink_id>/favorite/delete", methods=['GET', 'POST'])
def delete_favorite(drink_id):
    """Delete user favorite from database"""

    f = Favorite.query.filter_by(drink_id=drink_id, user_id=g.user.id).first()


    if f:
        db.session.delete(f)
        db.session.commit()
        flash('Delete successful', 'seccess')
        return redirect(url_for('show_drink_details', drink_id=drink_id))
    else:
        flash('Favorite not found', 'danger')
        return redirect(url_for('show_drink_details', drink_id=drink_id))


@app.route('/drink/<int:drink_id>')
def drink_details(drink_id):

    drink = Drink.query.get_or_404(drink_id)
    return render_template('drink-details.html', drink=drink, check_author=check_author)

@app.route("/<int:drink_id>")
def show_drink_details(drink_id):
    """Show details for a specific drink"""

    drink = Drink.query.get_or_404(drink_id)
    ingredients = drink.ingredients
    likes = len(drink.favorites)

    return render_template(
        "drink-details.html",
        drink=drink,
        ingredients=ingredients,
        User=User,
        Ingredient=Ingredient,
        DrinkPost=DrinkPost
    )


@app.route("/drinks/category/<int:category_id>")
def show_category_drinks(category_id):
    """Show all drinks in a category"""

    category = Category.query.get_or_404(category_id)
    drinks = category.drinks
    drink_count = len(drinks)
    stop_at = 50

    return render_template("drinks.html", drinks=drinks, title=f"{category.name}", drink_count=drink_count, stop_at=stop_at)

@app.route("/drinks/add", methods=["GET", "POST"])
def add_drink():
    """Add user drink to database"""

    form = DrinkForm()

    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    form.category_id.choices.insert(0, (None, "Select the category"))
    

    try:
        if form.validate_on_submit():
            if g.user:
                if form.category_id.data != 'None':
                    d = Drink(
                        name=form.name.data,
                        category_id=form.category_id.data,
                        image=form.image.data,
                    )

                    db.session.add(d)
                    db.session.commit()

                    dp = DrinkPost(user_id=g.user.id, drink_id=d.id)

                    db.session.add(dp)
                    db.session.commit()

                    flash(
                        f"{d.name} has been added, now for the ingredients!",
                        "success",
                    )
                    flash('If optional measurements are missing their conterpart, they will be ignored.', 'info')
                    return redirect(f"/{d.id}/ingredients/add")
                else:
                    flash(
                        "A category must be selected before adding a drink!",
                        "warning",
                    )
                    return render_template("add-drink.html", form=form)
            else:
                flash('You must be logged in to add a drink!', 'warning')
                return redirect('/login')
        else:
            return render_template("add-drink.html", form=form)
    except IntegrityError:
        flash('Sorry, that drink name is taken!', 'warning')
        return redirect('/drinks/add')


@app.route("/<int:drink_id>/ingredients/add", methods=["GET", "POST"])
def add_ingredients(drink_id):
    """Add ingredients and measurements to go with new drink (max 15 ingredient-measurement pairs)"""
    d = Drink.query.get_or_404(drink_id)
    bad_ans = ['None', None, '']

    form = IngredientsForm()
    for field in form:
        field.choices = [
            (i.id, i.name) for i in Ingredient.query.order_by(Ingredient.name).all()
        ]

        if field.choices:
            field.choices.insert(0, (None, 'Select an ingredient'))
        else:
            field.choices = (None, "Select an ingredient")

    if form.validate_on_submit():
        count = 0
        if g.user:
            d_p = DrinkPost.query.filter(DrinkPost.drink_id == d.id, DrinkPost.user_id == g.user.id).first()
            if d_p:
                for field in form:
                    count += 1
                    if "ingredient" in field.id and field.data not in bad_ans:
                        d_i = DrinkIngredient(drink_id=d.id, ingredient_id=field.data)

                    elif "measurement" in field.id and field.data not in bad_ans:
                        if d_i:
                            d_i.measurement = field.data
                            db.session.add(d_i)
                            d_i = None

                    elif field.data in bad_ans and count >= 3:
                        print(f'idx = {count}, data = {field.data}')
                        if count == 3:
                            db.session.commit()
                            flash(f'{d.name} has been added, thanks for your contribution!', 'success')
                            return redirect(f"/{d.id}")
                    
                        elif count % 2 == 0:
                            db.session.rollback()
                            flash('Each ingredient must have a measurement!', 'warning')
                            return redirect(f'/{d.id}/ingredients/add')
                        else:
                            db.session.commit()
                            flash(f'{d.name} has been added, thanks for your contribution!', 'success')
                            return redirect(f"/{d.id}")

                    else:
                        db.session.rollback()
                        flash('One ingredient and measurement required!', 'warning')
                        return redirect(f'/{d.id}/ingredients/add')
            else:
                db.session.rollback()
                flash('You must be the author of the drink to edit ingredients!', 'danger')
                return redirect('/')
        else:
            flash('You must be logged in to access this feature!', 'warning')
            return redirect('/')
    else:
        return render_template("add-ingredients.html", form=form, drink=d)

@app.route("/delete/<int:drink_id>")
def delete_drink(drink_id):
    """If author is g.user delete drink and redirect to profile"""

    if g.user:
        drink = Drink.query.get_or_404(drink_id)
        post = DrinkPost.query.filter(
            DrinkPost.drink_id == drink_id, DrinkPost.user_id == g.user.id
        ).first()

        if post:
            db.session.delete(drink)
            db.session.delete(post)
            db.session.commit()

            flash(f"{drink.name} has now been deleted!", "warning")
            return redirect(f"/profile/{g.user.id}")
        else:
            flash("Sorry, only the author of this drink post can delete it!", "danger")
            return redirect(f"/")
    else:
        flash('You must be logged in to access this feature!', 'warning')
        return redirect('/')


@app.route("/<int:drink_id>/edit", methods=['GET', 'POST'])
def edit_drink(drink_id):
    '''Edit drink form'''

    drink = Drink.query.get_or_404(drink_id)
    form = DrinkForm(obj=drink)

    form.category_id.choices = [
        (c.id, c.name) for c in Category.query.order_by(Category.name).all()
    ]
    form.category_id.choices.insert(0, (None, 'Select category'))

    if form.validate_on_submit():
        if g.user:
            if form.category_id.data != 'None':
                if DrinkPost.query.filter(
                    DrinkPost.drink_id == drink_id, DrinkPost.user_id == g.user.id
                ).first():
                    drink.name = form.name.data or drink.name
                    drink.category_id = form.category_id.data or drink.category_id
                    drink.instructions = form.instructions.data or drink.instructions
                    drink.image = form.image.data or drink.image

                    db.session.add(drink)
                    db.session.commit()

                    flash('You have made changes', 'success')
                    return redirect(f'/{drink.id}')
                else:
                    flash('Only the author can edit', 'danger')
            else:
                flash('A category must be selected', 'warning')
                return render_template('edit-drink.html', form=form, drink=drink)
        else:
            flash('Login in to edit drinks', 'warning')
            return redirect('/')
    else:
        return render_template('edit-drink.html', form=form, drink=drink)


@app.route('/<int:drink_id>/<int:ingredient_id>/edit', methods=['GET', 'POST'])
def edit_drink_ingredient(drink_id, ingredient_id):
    """If author is g.user edit drink ingredient and redirect to drink page"""
    
    d_i = DrinkIngredient.query.filter(DrinkIngredient.drink_id == drink_id, DrinkIngredient.ingredient_id == ingredient_id).first()
    drink = Drink.query.get_or_404(drink_id)
    form = EditDrinkIngredientForm(obj=d_i)
    form.ingredient_id.choices = [
            (i.id, i.name) for i in Ingredient.query.order_by(Ingredient.name).all()
        ]
    form.ingredient_id.choices[0] = (None, "Select an ingredient")

    if form.validate_on_submit():
        if g.user:
            post = DrinkPost.query.filter(
                DrinkPost.drink_id == drink_id, DrinkPost.user_id == g.user.id
            ).first()

            if post:
                if form.ingredient_id.data == 'None': form.ingredient_id.data = d_i.ingredient.id

                d_i.ingredient_id = form.ingredient_id.data
                d_i.measurement = form.measurement.data

                db.session.commit()

                flash(f'{drink.name} has been updated!', 'success')
                return redirect(f'/{drink.id}')
            else:
                flash("Sorry, only the author of this drink can edit ingredients!", "danger")
                return redirect(f"/")
        else:
            flash('You must be logged in to access this feature!', 'warning')
            return redirect('/')
    else:
        return render_template('edit-ingredient.html', form=form, drink=drink)
    

@app.route('/<int:drink_id>/<int:ingredient_id>/delete')
def delete_drink_ingredient(drink_id, ingredient_id):
    """If author is g.user delete drink ingredient"""

    if g.user:
        d_i = DrinkIngredient.query.filter(DrinkIngredient.drink_id == drink_id, DrinkIngredient.ingredient_id == ingredient_id).first()
        post = DrinkPost.query.filter(DrinkPost.drink_id == drink_id, DrinkPost.user_id == g.user.id).first()

        if post:
            db.session.delete(d_i)
            db.session.commit()

            flash('Ingredient has been deleted!', 'warning')
            return redirect(f'/{drink_id}')
        else:
            flash("Sorry, only the author of this drink can delete ingredients!", "danger")
            return redirect(f"/")    

    else:
        flash('You must be logged in to access this feature!', 'warning')
        return redirect('/')


@app.route("/search", methods=["POST"])
def show_search_results():
    """Query database for any matching drinks and display results"""

    form = SearchForm()

    if form.validate_on_submit():
        if g.user:
            q = form.search.data
            results = get_search_results(q)
            
            return render_template(
                "drinks.html",
                drinks=results,
                title=f"{len(results)} Search Results for '{q}'",
            )
        else:
            flash('You must be logged in to access this feature!', 'warning')
        return redirect('/')
    else:
        flash("Something went wrong, please try again!", "warning")
        return redirect("/")


def get_search_results(q):
    """Search DB for input string"""

    results = []

    ingredients = Ingredient.query.filter(
        Ingredient.name.ilike(f"%{q}%")).all()
    if ingredients:
        for ingredient in ingredients:
            for drink in ingredient.drinks:
                if drink.drink != None:
                    results.append(drink.drink)

    categories = Category.query.filter(Category.name.ilike(f"%{q}%")).all()
    if categories:
        for category in categories:
            for drink in category.drinks:
                if drink != None and drink not in results:
                    results.append(drink)

    drinks = Drink.query.filter(Drink.name.ilike(f"%{q}%")).all()
    if drinks:
        for drink in drinks:
            if drink != None and drink not in results:
                results.append(drink)

    return results