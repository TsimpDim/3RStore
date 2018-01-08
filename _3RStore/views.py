from time import time
import datetime
from _3RStore import app, conn
import psycopg2.extras
from bs4 import BeautifulSoup
from flask import request, session, redirect, url_for, render_template, flash, abort, make_response
from passlib.hash import sha256_crypt
from . import forms


@app.route('/')
def index():
    return render_template('home.html')

# About
@app.route('/about')
def about():
    return render_template('about.html')


# User Registration
@app.route('/register', methods=['GET', 'POST'])
def register():

    form = forms.RegisterForm(request.form)
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
        cur.execute(("""
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

# Options
@app.route('/options')
def options():
    sort = request.cookies.get('sort')
    criteria = request.cookies.get('criteria')
    return render_template('options.html', sort=sort, criteria=criteria)

# Sorting order
@app.route('/options/set_sort/<string:criteria>/<string:stype>')
def set_asc(criteria, stype):
    resp = make_response(redirect(url_for('options')))
    resp.set_cookie('sort', stype)
    resp.set_cookie('criteria', criteria)
    return resp

# Resources
@app.route('/resources')
def resources():

    if not session.get('logged_in'):
        flash('You must be logged in to access your resources page', 'warning')
        return redirect(url_for('login'))
    else:
        user_id = session['user_id']

        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        sort = request.cookies.get('sort')
        criteria = request.cookies.get('criteria')
        if criteria == 'title':
            if sort == 'asc' or not sort:
                cur.execute(
                    ("""SELECT * FROM resources WHERE user_id = %s ORDER BY title ASC"""),
                    (user_id,)
                )
            else:
                cur.execute(
                    ("""SELECT * FROM resources WHERE user_id = %s ORDER BY title DESC"""),
                    (user_id,)
                )
        elif criteria == 'time' or not criteria:
            if sort == 'asc' or not sort:
                cur.execute(
                    ("""SELECT * FROM resources WHERE user_id = %s ORDER BY date_of_posting ASC"""),
                    (user_id,)
                )
            else:
                cur.execute(
                    ("""SELECT * FROM resources WHERE user_id = %s ORDER BY date_of_posting DESC"""),
                    (user_id,)
                )

        data = cur.fetchall()
        cur.close()
        conn.commit()
        return render_template('resources.html', resources=data, sort=sort)

    return render_template('resources.html')


# Add resource
@app.route('/add_resource', methods=['GET', 'POST'])
def add_resource():

    form = forms.ResourceForm(request.form)
    if request.method == 'POST' and form.validate():
        title = form.title.data
        link = form.link.data
        note = form.note.data
        timestamp = datetime.datetime.fromtimestamp(
            time()).strftime('%Y-%m-%d %H:%M:%S')

        tags = form.tags.data
        # If not empty format for proper insertion into postgresql
        if tags:
            tags = '{' + str(tags) + '}'
        else:
            tags = None

        user_id = session['user_id']


        cur = conn.cursor()
        cur.execute(
            ("""INSERT INTO resources(user_id,title,link,note,tags,date_of_posting) VALUES (%s,%s,%s,%s,%s,%s)"""),
            (user_id, title, link, note, tags, timestamp)
            )
        cur.close()
        conn.commit()

        flash('Resource created successfully', 'success')
        return redirect(url_for('resources'))
    return render_template('add_resource.html', form=form)

# Delete resource
@app.route('/del/<int:user_id>/<int:re_id>')
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
@app.route('/edit/<int:user_id>/<int:re_id>', methods=['GET', 'POST'])
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
            form = forms.ResourceForm()
            form.title.data = data[0]['title']
            form.link.data = data[0]['link']
            form.note.data = data[0]['note']

            if data[0]['tags']:
                form.tags.data = ','.join(data[0]['tags']) # Array to string
            else:
                form.tags.data = ""

            return render_template('edit_resource.html', title=data[0]['title'], form=form)

    elif request.method == 'POST':

        form = forms.ResourceForm(request.form)
        if form.validate():

            # Grab the new form and its data
            title = form.title.data
            link = form.link.data
            note = form.note.data
            tags = form.tags.data

            # If not empty format for proper insertion into postgresql
            if tags:
                tags = '{' + str(tags) + '}'
            else:
                tags = None

            # Update the row - keep date_of_posting, re_id and user_id the same
            cur = conn.cursor()
            cur.execute(
                ("""UPDATE resources SET title=%s,link=%s,note=%s,tags=%s WHERE user_id=%s AND re_id=%s"""),
                (title, link, note, tags, user_id, re_id)
                )
            cur.close()
            conn.commit()

            flash('Resource edited successfully', 'success')
            return redirect(url_for('resources'))
        else:
            return render_template('edit_resource.html', form=form)
    return redirect(url_for('resources'))

# Delete all resources
@app.route("/delall/<int:user_id>")
def delall(user_id):

    if session['user_id'] == user_id and session.get('logged_in'):
        cur = conn.cursor()
        cur.execute("""DELETE FROM resources WHERE user_id = %s""", (user_id,))
        cur.close()
        conn.commit()
        flash('All resources deleted.', 'danger')

    return redirect(url_for('resources'))


# Import resources
@app.route("/import_resources" , methods = ['GET', 'POST'])
def import_resources():

    if request.method == 'POST':

        if 'file' not in request.files:
            flash('No file selected', 'warning')
            return redirect(request.url)
        else:

            file = request.files['file']
            if file.filename == '':
                flash('No file selected', 'warning')
                return redirect(request.url)

            if file:

                soup = BeautifulSoup(file, "html.parser")
                cur = conn.cursor()

                folders = soup.find_all('dl')
                for folder in folders:

                    header = folder.find_previous_sibling("h3")

                    if header: # We filter the first DL which has an H1 tag before it and is not a 'folder'

                        tag = '{' + str(header.contents[0]) + '}'

                        for resource in folder.findChildren('a'):
                            link = resource['href']

                            if resource.contents:
                                title = resource.contents[0][0:99]
                            else:
                                title = link[0:50] + '...'

                            timestamp = datetime.datetime.fromtimestamp(
                                time()).strftime('%Y-%m-%d %H:%M:%S')
                            user_id = session['user_id']


                            cur.execute(
                                ("""INSERT INTO resources(user_id,title,link,tags,date_of_posting) VALUES (%s,%s,%s,%s,%s)"""),
                                (user_id, title, link, tag, timestamp)
                            )

                cur.close()
                conn.commit()
                flash('Resources imported successfully', 'success')

    return redirect(url_for('resources'))
