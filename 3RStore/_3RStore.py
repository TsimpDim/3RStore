import json
import psycopg2 as pg
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import  Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt

app = Flask(__name__)
app.config.from_object(__name__)

# Connect to PostgreSQL
# Read database properties for URI
DB_CONFIG = json.load(open('db.json'))
USER = DB_CONFIG['user']
PASSWORD = DB_CONFIG['password']
HOST = DB_CONFIG['host']
NAME = DB_CONFIG['database']

try:
    print("Connecting to database...")

    conn = pg.connect(("dbname={} user={} host={} password={}").format(NAME, USER, HOST, PASSWORD))
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Users (
        email varchar(120) NOT NULL,
        username varchar(45) NOT NULL,
        password varchar(45) NOT NULL,
        PRIMARY KEY (email)
        )""")
    cur.close()
    conn.commit()
except (Exception, pg.DatabaseError) as error:
    print("Unable to connect to the database" + error)



@app.route('/')
def index():
    return render_template('home.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/resources')
def resources():
    return render_template('resources.html')

@app.route('/register')
def register():
    return render_template('register.html')

if __name__ == '__main__':
    app.run(debug=True)
