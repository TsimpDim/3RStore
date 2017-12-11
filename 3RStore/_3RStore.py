import json
import datetime
from time import time
import re
import psycopg2.extras
import psycopg2 as pg
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
        """CREATE TABLE IF NOT EXISTS users (
        id SERIAL,
        email varchar(50) NOT NULL,
        username varchar(45) NOT NULL,
        password varchar(100) NOT NULL,
        date_of_reg timestamp NOT NULL,
        PRIMARY KEY (id)
        )""")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS resources (
        re_id SERIAL,
        user_id INT NOT NULL REFERENCES users(id),
        title varchar(100) NOT NULL,
        link TEXT NOT NULL,
        note TEXT,
        date_of_posting timestamp NOT NULL,
        PRIMARY KEY (re_id)
        )""")
    
    cur.close()
    conn.commit()
except (Exception, pg.DatabaseError) as error:
    print("Unable to connect to the database" + error)


@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')

# Register Form Class
class RegisterForm(Form):
    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=5, max=45)
    ])
    email = StringField('Email', [
        validators.DataRequired(),
        validators.Length(min=8, max=50),
        validators.Email()
        ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])

    confirm = PasswordField('Confirm Password')

# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():

    form = RegisterForm(request.form)
    if request.method == 'POST' and form.validate():
        username = form.username.data
        email = form.email.data
        password = sha256_crypt.encrypt(str(form.password.data)) # Encrypt the password using sha256
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
        return redirect(url_for('login'))

    return render_template('register.html', form=form)

# User Login
@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        # Grab the fields from the form
        username = request.form['username']
        password_candidate = request.form['password']


        # And get the user from the db
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # Treat result as a dictionary
        get_user = cur.execute(("""
        SELECT * FROM users WHERE username = %s
        """), (username,)) # Comma for single element tuple

        # If we find a user with that username
        data = cur.fetchone()
        if data:
            app.logger.info('USER FOUND')
            password = data['password']

            # Validate pass
            if sha256_crypt.verify(password_candidate, password):
                session['logged_in'] = True
                session['username'] = username
                session['user_id'] = data['id']

                flash('You are now logged in', 'success')
                return redirect(url_for('resources'))
            else:
                error = "Username or password are incorrect"
                return render_template('login.html', error=error)
        else:
            error = "Username or password are incorrect"
            return render_template('login.html', error=error)

        cur.close()
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    flash('You are now logged out', 'success')
    return redirect('/')

# Resources
@app.route('/resources')
def resources():

    if not session.get('logged_in'):
        flash('You must be logged in to access your resources page', 'warning')
        return redirect(url_for('login'))
    else:
        user_id = session['user_id']

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            ("""SELECT * FROM resources WHERE user_id = %s ORDER BY date_of_posting"""),
            (user_id,)
            )

        data = cur.fetchall()
        cur.close()
        conn.commit()
        return render_template('resources.html', resources=data)

    return render_template('resources.html')

# Resource Form Class
class ResourceForm(Form):
    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=1, max=100)
    ])
    link = StringField('Link', [
        validators.DataRequired(),
        validators.URL()
        ])
    note = TextAreaField('Note')


# Add resource
@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():

    form = ResourceForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        link = form.link.data
        note = form.note.data
        timestamp = datetime.datetime.fromtimestamp(
            time()).strftime('%Y-%m-%d %H:%M:%S')
        user_id = session['user_id']

        cur = conn.cursor()
        cur.execute(
            ("""INSERT INTO resources(user_id,title,link,note,date_of_posting) VALUES (%s,%s,%s,%s,%s)"""),
            (user_id, title, link, note, timestamp)
            )
        cur.close()
        conn.commit()

        flash('Resource created successfully', 'success')
        return redirect(url_for('resources'))
    return render_template('add_resource.html', form=form)

# Delete resource
@app.route('/del/<int:user_id>,<int:re_id>')
def delete_res(user_id,re_id):

    if session.get('logged_in') and session['user_id'] == user_id:
        cur = conn.cursor()
        cur.execute(
            ("""DELETE FROM resources WHERE user_id = %s and re_id = %s"""),
            (user_id, re_id)
            )

        cur.close()
        conn.commit()
    return redirect(url_for('resources'))

# Edit resource
@app.route('/edit/<int:user_id>,<int:re_id>', methods=['GET', 'POST'])
def edit_res(user_id,re_id):

    if request.method == 'GET':
        if session.get('logged_in') and session['user_id'] == user_id:

            # Fetch the data we want to edit
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                ("""SELECT * FROM resources WHERE user_id = %s and re_id = %s"""),
                (user_id, re_id)
                )

            data = cur.fetchall()
            cur.close()
            conn.commit()

            # Fill the form with the data
            form = ResourceForm()
            form.title.data = data[0]['title']
            form.link.data = data[0]['link']
            form.note.data = data[0]['note']

            return render_template('edit_resource.html', title=data[0]['title'], form=form)

    elif request.method == 'POST':

        form = ResourceForm(request.form)
        if form.validate():
            # Grab the new form and its data
            title = form.title.data
            link = form.link.data
            note = form.note.data

            # Update the row - keep date_of_posting, re_id and user_id the same
            cur = conn.cursor()
            cur.execute(
                ("""UPDATE resources SET title=%s,link=%s,note=%s WHERE user_id=%s AND re_id=%s"""),
                (title, link, note, user_id, re_id)
                )
            cur.close()
            conn.commit()

            flash('Resource edited successfully', 'success')
            return redirect(url_for('resources'))
    return redirect(url_for('resources'))


if __name__ == '__main__':

    # Read secret key from file
    try:
        app.config['SECRET_KEY'] = open("seckey.txt", 'rb').read()
        print("Read secret key succesfully")
    except IOError:
        print("Error: No secret key.")
    app.run(debug=True)
