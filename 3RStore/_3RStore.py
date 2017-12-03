import os
import json
import psycopg2 as pg
from time import time
import datetime
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
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

conn = None  # Declared here so we can use it later
try:
    print("Connecting to database...")

    conn = pg.connect(("dbname={} user={} host={} password={}").format(
        NAME, USER, HOST, PASSWORD))
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS Users (
        id SERIAL,
        email varchar(50) NOT NULL,
        username varchar(45) NOT NULL,
        password varchar(100) NOT NULL,
        date_of_reg timestamp NOT NULL,
        PRIMARY KEY (id)
        )""")
    cur.close()
    conn.commit()
except (Exception, pg.DatabaseError) as error:
    print("Unable to connect to the database" + error)


@app.route('/')
@app.route('/home')
def index():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/resources')
def resources():
    return render_template('resources.html')


class RegisterForm(Form):
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=5, max=45)
    ])
    email = StringField('Email', [
        validators.DataRequired(),
        validators.Length(min=8, max=50)])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])

    confirm = PasswordField('Confirm Password')


@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        # Encrypt the password using sha256
        password = sha256_crypt.encrypt(str(form.password.data))
        timestamp = datetime.datetime.fromtimestamp(
            time()).strftime('%Y-%m-%d %H:%M:%S')

        if not conn:
            flash('Could not connect to database', 'error')
        else:
            cur = conn.cursor()
            cur.execute(
                ("""INSERT INTO users(email,username,password,date_of_reg) VALUES (%s,%s,%s,%s)"""), (
                    email, username, password, timestamp)
            )

            cur.close()
            conn.commit()

        flash('You are now registered', 'success')
        # return redirect(url_for('about'))

    return render_template('register.html', form=form)


if __name__ == '__main__':

    # Read secret key from file
    try:
        app.config['SECRET_KEY'] = open("seckey.txt", 'rb').read()
        print("Read secret key succesfully")
    except IOError:
        print("Error: No secret key.")
    app.run(debug=True)
