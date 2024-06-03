import pandas
import psycopg2
import os

USER_CSV = '/generator/user.csv'
COCKTAIL_CSV = '/generator/cocktail.csv'
cocktails = pandas.read_csv(COCKTAIL_CSV)
cocktails.columns = [c.replace(' ', '_') for c in cocktails.columns]
cocktail_attributes = cocktails[['Cocktail_Name', 'Ingredients', 'Preperation']]
main_cocktail_atttributes = [['Cocktail_Name', 'Preperation']]

ENV = 'dev'

if ENV == 'dev':
    password = os.environ.get('POSTGRES_PASS')
    con = psycopg2.connect(database='cocktailpg', user='postgres', password={password}, host='127.0.0.1')
else:
    con = psycopg2.connect(os.environ.get('DATABASE_URL'))
cursor = con.cursor()
con.autocommit = True

def double_apostrophe(string):
    final = ''
    for c in string:
        if c == "'":
            final += "'" * 2
    else:
        final += c
    return final


def create_db():
    create_commands = """

    DROP TABLE IF EXISTS cocktails CASCADE;
    CREATE TABLE cocktails
    (
        id SERIAL,
        name TEXT NOT NULL,
        prep TEXT,
        PRIMARY KEY (id)
    );

    DROP TABLE IF EXISTS ingredients CASCADE;
    CREATE TABLE ingredients
    (
        id SERIAL,
        name TEXT NOT NULL,
        PRIMARY KEY (id)
    );

    DROP TABLE IF EXISTS cocktail_ingredients CASCADE;
    CREATE TABLE cocktail_ingredients
    (
        cocktail_id INTEGER,
        ingredient_id INTEGER,
        FOREIGN KEY(cocktail_id), REFERENCES cocktails(id)
        FOREIGN KEY(ingredients_id), REFERENCES ingredients(id)
    );
    """
    cursor.execute(create_commands)
    con.commit()


def initial_table_insert(dataset, table_name):
    for e in dataset:
        if "'" in e:
            e = double_apostrophe(string=e)
        e = e.strip()
        cursor.execute(f"INSERT INTO {table_name} (name) VALUES('{e}') RETURNING id;")
        con.commit()


def normalize_rows(column):
    item_set = set()
    for row in column:
        if type(row) != float:
            list_row = row.split(',')
            if len(list_row) == 1:
                item_set.add(row)
            else:
                for e in list_row:
                    item_set.add(e)

    return item_set


def insert_data_into_cocktails():
    for row in main_cocktail_atttributes.itertuples():
        name = row[1]
        prep = row[2]
        if "'" in name:
            name = double_apostrophe(string=name)
        if type(prep) == str and "'" in prep:
            prep = double_apostrophe(string=prep)
        cursor.execute(f"INSERT INTO cocktails (name, prep) VALUES ('{name}', '{prep}') RETURNING id;")
        con.commit()


def insert_cocktail_ingredients():
    cocktail_ingredients = cocktails[['Cocktail_Name', 'Ingredients']]
    for row in cocktail_ingredients.itertuples():
        cocktail_name = row[1]
        if "'" in cocktail_name:
            cocktail_name = double_apostrophe(string=cocktail_name)
        ingredients = row[2]
        if type(ingredients) != float:
            cursor.execute(f"SELECT id from cocktails WHERE name = '{cocktail_name}';")
            cocktail_id = cursor.fetchone()[0]
            ingredient_list = ingredients.split(',')
            for ingredient in ingredient_list:
                if "'" in ingredient:
                    ingredient = double_apostrophe(string=ingredient)
                ingredient = f" '{ingredient.strip()}' "
                cursor.execute(f"SELECT id from ingredients WHERE name = {ingredient};")
                ingredient_id = cursor.fetchone()[0]
                cursor.execute(
                    f"INSERT INTO cocktail_ingredients (cocktail_id, ingredient_id) VALUES ({cocktail_id}, {ingredient_id})")
                con.commit()


def add_user_table():
    create_commands = '''
    DROP TABLE IF EXISTS users CASCADE;
    CREATE TABLE users
    (
        id SERIAL,
        username TEXT,
        password TEXT,
        email TEXT,
        PRIMARY KEY (id)
    );
    DROP TABLE IF EXISTS saved_cocktails CASCADE;
    CREATE TABLE saved_cocktails
    (
        user_id INTEGER,
        cocktail_id INTEGER,
        FOREIGN KEY(user_id) REFERENCES users(id),
        FOREIGN KEY(cocktail_id) REFERENCES cocktails(id)
    );'''


def db_init():
    create_db()
    initial_table_insert(dataset=normalize_rows(column=cocktails.Ingredients), table_name='ingredients')
    insert_data_into_cocktails()
    insert_cocktail_ingredients
    add_user_table()
    con.commit()
    con.close()

db_init()