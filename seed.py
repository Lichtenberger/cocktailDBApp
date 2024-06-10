from app import app
from models import Drink, User, Ingredient, Category, DrinkIngredient, db
from time import sleep
from alive_progress import alive_bar
import random
import requests

base_url = 'https://www.thecocktaildb.com/api/json/v1/1/'

with app.app_context():
    db.drop_all()
    db.create_all()

def add_categories():
    res = requests.get(base_url + 'list.php', params={'c': 'list'})
    categories = res.json()
    with alive_bar(len(categories['drinks']), title='Adding categories:', length=25) as bar:
        for category in categories['drinks']:
            c = Category(name=category['strCategory'].title())
            db.session.add(c)
            db.session.commit()
            bar()

def add_ingredients():
    res = requests.get(base_url + 'list.php', params={'i': 'list'})
    ingredients = []
    ingredients_raw = res.json()
    for ingredient in ingredients_raw['drinks']:
        ingredients.append(ingredient['strIngredient1'])
    with alive_bar(len(ingredients), title='Adding ingredients:', length=25) as bar:
        ing_list = []
        for ingredient in ingredients:
            res = requests.get(base_url + 'search.php', params={'i': f"{ingredient}"})
            ings = res.json()
            i = Ingredient(
                name=ings['ingredients'][0]['strIngredient'].title(),
                description=ings["ingredients"][0]["strDescription"],
                abv=ings['ingredients'][0]['strABV'],)
            ing_list.append(i)
            bar()
        db.session.add_all(ing_list)
        db.session.commit()

def add_all_drinks():
    with app.app_context():
        categories = Category.query.all()
        with alive_bar(len(categories), length=25) as bar:
            for category in categories:
                bar.title = f"Adding {category.name} drinks:"
                res = requests.get(base_url + 'filter.php', params={'c': f"{category.name}"})
                drinks = res.json()
                drink_list = []
                for drink in drinks['drinks']:
                    d = Drink(
                        name=drink['strDrink'],
                        api_id=drink['idDrink'],
                        image=drink['strDrinkThumb'],)
                    drink_list.append(d)
                db.session.add_all(drink_list)
                db.session.commit()
                bar()

def add_drink_ingredients():
    with app.app_context():
        drinks = Drink.query.all()
        with alive_bar(len(drinks), length=20, title_length=20) as bar:
            for drink in drinks:
                bar.title = f"Adding {drink.name}:"
                try:
                    res = requests.get(base_url + 'lookup.php', params={'i': f'{drink.api_id}'})
                except:
                    print('API is overloaded chill a little')
                    sleep(5)
                    res = requests.get(base_url + 'lookup.php', params={'i': f'{drink.api_id}'})
                sleep(random.uniform(2.00, 4.50))
                details = res.json()
                data = details['drinks'][0]
                category = Category.query.filter_by(name=data['strCategory'].title()).first()
                drink.category_id = category.id
                drink.instructions = data['strInstructions']
                count = 1
                drink_ings = []
                while data[f'strIngredient{count}'] is not None:
                    ingredient = Ingredient.query.filter_by(name=data[f'strIngredient{count}'].title()).first()
                    if ingredient is None:
                        i = Ingredient(name=data[f'strIngredient{count}'].title())
                        db.session.add(i)
                        db.session.commit()
                        d_i = DrinkIngredient(
                            drink_id=drink.id,
                            ingredient_id=i.id,
                            measurement=data[f'strMeasure{count}'],)
                        drink_ings.append(d_i)
                    else:
                        d_i = DrinkIngredient(
                            drink_id=drink.id,
                            ingredient_id=ingredient.id,
                            measurement=data[f'strMeasure{count}'],)
                        drink_ings.append(d_i)
                    count += 1
                db.session.add_all(drink_ings)
                db.session.commit()
                bar()

add_categories()
sleep(5)
add_ingredients()
sleep(5)
add_all_drinks()
sleep(15)
add_drink_ingredients()