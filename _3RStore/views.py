from time import time
import datetime
from _3RStore import app, conn
from psycopg2 import DatabaseError
import psycopg2.extras
from bs4 import BeautifulSoup
from flask import request, session, redirect, url_for, render_template, flash, make_response, send_file
from passlib.hash import sha256_crypt
from . import forms
from io import BytesIO


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
        # Treat result as a dictionary
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(("""
        SELECT * FROM users WHERE username = %s
        """), (username,))  # Comma for single element tuple

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

                # Set default cookies if they don't exist
                # Build default response
                resp = make_response(redirect(url_for('resources')))

                sort = request.cookies.get('sort')
                criteria = request.cookies.get('criteria')
                if not sort or not criteria:  # If any of them have not been set
                    resp.set_cookie(
                        'sort', "desc", expires=datetime.datetime.now()
                        + datetime.timedelta(days=30))

                    resp.set_cookie(
                        'criteria', "time", expires=datetime.datetime.now()
                        + datetime.timedelta(days=30))

                flash('You are now logged in', 'success')
                return resp
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

    if session.get('logged_in'):
        sort = request.cookies.get('sort')
        criteria = request.cookies.get('criteria')
        return render_template('options.html', sort=sort, criteria=criteria)
    else:
        flash('You must be logged in to access the options page', 'warning')
        return redirect(url_for('login'))

# Sorting order
@app.route('/options/set_sort/<string:criteria>/<string:stype>')
def set_asc(criteria, stype):
    if session.get('logged_in'):
        resp = make_response(redirect(url_for('options')))
        resp.set_cookie(
            'sort', stype, expires=datetime.datetime.now()
            + datetime.timedelta(days=30))

        resp.set_cookie(
            'criteria', criteria, expires=datetime.datetime.now()
            + datetime.timedelta(days=30))

        return resp
    else:
        flash('You must be logged in to access the options page', 'warning')
        return redirect(url_for('login'))

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

        cur.execute(
            ("""SELECT DISTINCT unnest(tags) FROM resources WHERE user_id = %s"""),
            (user_id,)
        )

        tags_raw = cur.fetchall()

        # 'Unpack' tags_raw into one array
        all_tags = []
        for tag_arr in tags_raw:
            all_tags.append(tag_arr[0])

        cur.close()
        conn.commit()
        return render_template('resources.html', resources=data, sort=sort, tags=all_tags)

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
            tags = '{' + str(tags).lower() + '}'
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
    else:
        user_id = session['user_id']
        cur = conn.cursor()
        cur.execute(
            ("""SELECT DISTINCT unnest(tags) FROM resources WHERE user_id = %s"""),
            (user_id,)
        )

        tags_raw = cur.fetchall()

        # 'Unpack' tags_raw into one array
        all_tags = []
        for tag_arr in tags_raw:
            all_tags.append(tag_arr[0])

        cur.close()
        return render_template('add_resource.html', form=form, tags=all_tags)

# Delete resource
@app.route('/del/<int:user_id>/<int:re_id>')
def delete_res(user_id, re_id):

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
def edit_res(user_id, re_id):

    if request.method == 'GET':
        if session.get('logged_in') and session['user_id'] == user_id:

            # Fetch the data we want to edit
            cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
            cur.execute(
                ("""SELECT * FROM resources WHERE user_id = %s and re_id = %s"""),
                (user_id, re_id)
            )

            data = cur.fetchall()

            # Get the tags to suggest to the user
            cur.execute(
                ("""SELECT DISTINCT unnest(tags) FROM resources WHERE user_id = %s"""),
                (user_id,)
            )

            tags_raw = cur.fetchall()

            # 'Unpack' tags_raw into one array
            all_tags = []
            for tag_arr in tags_raw:
                all_tags.append(tag_arr[0])

            cur.close()
            conn.commit()

            # Fill the form with the data
            form = forms.ResourceForm()
            form.title.data = data[0]['title']
            form.link.data = data[0]['link']
            form.note.data = data[0]['note']

            if data[0]['tags']:
                form.tags.data = ','.join(data[0]['tags'])  # Array to string
                form.tags.data = form.tags.data.lower()
            else:
                form.tags.data = ""

            return render_template('edit_resource.html', title=data[0]['title'], form=form, tags=all_tags)

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
                tags = '{' + str(tags).lower() + '}'
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
@app.route("/import_resources", methods=['GET', 'POST'])
def import_resources():
    cur = conn.cursor()

    def add_res_to_db(resource, tags):

        # Transform tags to all lowercase
        tags = [tag.lower() for tag in tags]

        link = resource['href']

        if resource.contents:
            title = resource.contents[0][0:99]
        else:
            title = link[0:50] + '...'

        timestamp = datetime.datetime.fromtimestamp(
            time()).strftime('%Y-%m-%d %H:%M:%S')
        user_id = session['user_id']


        try:
            cur.execute(
                ("""INSERT INTO resources(user_id,title,link,tags,date_of_posting) VALUES (%s,%s,%s,%s,%s)"""),
                (user_id, title, link, tags, timestamp)
            )
        except DatabaseError:
            conn.rollback()


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

                soup = BeautifulSoup(file, "lxml")

                tags = []
                for curr_tag in soup.find_all():

                    if curr_tag.name.lower() == 'h3':
                        tags.append(curr_tag.contents[0])

                    elif curr_tag.name.lower() == 'a':
                        add_res_to_db(curr_tag, tags)

                    elif curr_tag.name.lower() == 'p' and tags \
                                                      and curr_tag.find_previous() \
                                                      and (curr_tag.find_previous().name == 'a' \
                                                      or curr_tag.find_previous().name == 'p'):
                        tags.pop()


                cur.close()
                conn.commit()
                flash('Resources imported successfully', 'success')

    return redirect(url_for('resources'))

@app.route('/export_to_html')
def export_to_html():
    def new_folder(main_tag, h3_text):
        dt_tag = soup.new_tag('DT')
        h3_tag = soup.new_tag('H3')
        dl_tag = soup.new_tag('DL')
        p_tag = soup.new_tag('P')

        h3_tag.string = h3_text

        dt_tag.append(h3_tag)
        dl_tag.append(p_tag)

        main_tag.append(dt_tag)
        main_tag.append(dl_tag)
        main_tag.append(soup.new_tag('P')) # To close each folder we created

    def new_link(main_tag, title, link):
        dt_tag = soup.new_tag('DT')
        
        a_tag = soup.new_tag('A')
        a_tag['HREF'] = link
        a_tag.string = title

        dt_tag.append(a_tag)
        main_tag.append(dt_tag)

    # Get all of the user's resources
    cur = conn.cursor()
    user_id = session['user_id']

    cur.execute(("""SELECT title, link, tags FROM resources WHERE user_id = %s"""),
    (user_id,)
    )

    user_resources = cur.fetchall()

    cur.execute(("""SELECT DISTINCT tags FROM resources WHERE user_id = %s"""),
    (user_id,)
    )

    user_tags = cur.fetchall()

    # Create base html
    soup = BeautifulSoup('<!DOCTYPE NETSCAPE-Bookmark-file-1>', 'lxml')
    meta_tag = soup.new_tag('META')
    meta_tag['HTTP-EQUIV'] = 'Content-Type'
    meta_tag['CONTENT'] = 'text/html; charset=UTF-8'
    soup.append(meta_tag)

    title_tag = soup.new_tag('TITLE')
    title_tag.string = '3RStore Resources'
    soup.append(title_tag)

    header_tag = soup.new_tag('H1')
    header_tag.string = '3RStore'
    soup.append(header_tag)

    dl_tag = soup.new_tag('DL')
    p_tag = soup.new_tag('P')
    p_tag['TYPE'] = 'Main'
    dl_tag.append(p_tag)
    soup.append(dl_tag)

    soup.append(soup.new_tag('P')) # <P> closing the final </DL>
    
    # Create the folders in HTML form
    for tag_array in user_tags:
        for i, tag in enumerate(tag_array[0]):

            root_folder_exists = soup.find('H3', string=tag_array[i-1][0])
            curr_folder_exists = soup.find('H3', string=tag)

            # If the root folder does not exist, create it
            if not root_folder_exists:
                main_tag = soup.find('P', {'TYPE' : 'Main'})
                new_folder(main_tag, tag_array[i-1][0])

            # If the root folder exists and we have not created this folder previously
            elif root_folder_exists and not curr_folder_exists:
                main_tag = soup.find('H3', string=tag_array[i-1][0]).find_next('DL')
                new_folder(main_tag, tag)

    # Insert the links in the corresponding folders
    for res in user_resources:
        title = res[0]
        link = res[1]
        tags = res[2]

        main_tag = soup.find('H3', string=tags[-1]).find_next('P')
        new_link(main_tag, title, link)

    # Save file
    # Clean up text - It's a hacky solution, i know
    final_text = str(soup).replace('</META>', '\n').replace('</TITLE>', '</TITLE>\n') \
    .replace('</H1>', '</H1>\n').replace('<DT>', '\n\t<DT>').replace('<DL>', '\n\t<DL>') \
    .replace('</DT>', '').replace('</P>', '').replace('</DL><P>', '\n\t</DL><P>')

    # Save text to byte object
    strIO = BytesIO()
    strIO.write(str.encode(final_text))
    strIO.seek(0)

    # Send html file to client
    return send_file(strIO, attachment_filename='3RStore_export.html', as_attachment=True)
