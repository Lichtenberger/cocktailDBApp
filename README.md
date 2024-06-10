API - www.thecocktaildb.com/api/json/v1/1/lookup.php?i=11007

An app using thecocktaildb api to search cocktails from a db.
Using technologies such as: Flask, Jinja, WTForms, PSQL

Simple site that allows you to sign up, and login to save your favorite cocktails. It also has the ability to allow you to add your own special concoctions if you desire. 

To install and start the app:
1. create directory
2. start virtual environment
3. clone repo make sure it is the master branch - https://github.com/Lichtenberger/cocktailDBApp 
4. pip install -r requirements.txt
5. sudo service postgresql start
6. createdb cocktailsdb
7. start ipython %run seed.py ** this step takes a while to load the db
8. flask run
9. open browser on localhost:5000