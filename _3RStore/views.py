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
from urllib import parse
from . import classes
from anytree import Node, RenderTree, find, AsciiStyle, NodeMixin, AnyNode


@app.before_request
def make_session_permanent():
    session.permanent = True

@app.route('/')
def index():
    return render_template('home.html')

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

# Delete account
@app.route('/delacc', methods=['POST'])
def delacc():
    user_id = request.form.get('user_id')

    cur = conn.cursor()
    try:
        # First delete from `resources` so as not to violate foreign key constraints
        cur.execute('DELETE FROM resources WHERE user_id = %s',
        (user_id,)
        )

        cur.execute('DELETE FROM users WHERE id = %s',
        (user_id,)
        )
    except DatabaseError:
        cur.rollback()

    session.clear()
    flash('Account deleted. Sad to see you go :(', 'danger')
    return redirect('/')

# Options
@app.route('/options')
def options():

    if session.get('logged_in'):
        sort = request.cookies.get('sort')
        criteria = request.cookies.get('criteria')

        # Get all tags
        cur = conn.cursor()
        user_id = session['user_id']

        cur.execute(
        ("""SELECT DISTINCT unnest(tags) FROM resources WHERE user_id = %s"""),
        (user_id,)
        )

        tags_raw = cur.fetchall()

        # 'Unpack' tags_raw into one array
        all_tags = []
        for tag_arr in tags_raw:
            all_tags.append(tag_arr[0])

        
        return render_template('options.html', sort=sort, criteria=criteria, tags=all_tags)
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

        try:
            cur.execute(
                ("""SELECT DISTINCT unnest(tags) FROM resources WHERE user_id = %s"""),
                (user_id,)
            )
        except DatabaseError:
            conn.rollbal()
            
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
        link = parse.unquote(form.link.data)
        note = form.note.data.replace('\n','</br>') # So we can show the newlines in the note section
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
            if form.note.data:
                form.note.data.replace('</br>','\n') # Else the </br> tags will display as text

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
            note = form.note.data.replace('\n','</br>') # Save newlines as </br> to display them properly later
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
@app.route("/delall", methods=['GET','POST'])
def delall():

    user_id = int(request.form.get('user_id'))
    if not user_id:
        flash('Something went wrong when handling your request', 'danger')
        return redirect(url_for('login'))

    if session['user_id'] == user_id and session.get('logged_in'):
        cur = conn.cursor()

        cur.execute("""DELETE FROM resources WHERE user_id = %s""", (user_id,))

        cur.close()
        conn.commit()
        flash('All resources deleted.', 'danger')
    return redirect(url_for('resources'))

# Filtered delete
@app.route("/fildel", methods=['POST'])
def fildel():

    tags_to_del = request.form.get('tags')
    user_id = session['user_id']

    tags_array = '{' + tags_to_del + '}'

    cur = conn.cursor()
    cur.execute(
    ("""DELETE FROM resources WHERE user_id = %s AND tags @> %s"""),
    (user_id, tags_array)
    )

    cur.close()
    conn.commit()

    flash('Resources deleted successfully', 'danger')
    return redirect(url_for('options'))

# Remove tag
@app.route("/remtag", methods=['POST'])
def remtag():

    tags = request.form.get('tags')

    if tags:
        tags_to_rem = tags.split(',')

        for tag in tags_to_rem:
            cur = conn.cursor()
            cur.execute("UPDATE resources SET tags = array_remove(tags, %s )",
            (tag,)
            )

        cur.close()
        conn.commit()

    flash('Tag(s) removed successfully', 'danger')
    return redirect(url_for('options'))

# Import resources
@app.route("/import_resources", methods=['GET', 'POST'])
def import_resources():
    cur = conn.cursor()

    def add_res_to_db(resource, tags):
        print("_ADD_DB")
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

    def search_and_insert(filters=None, incl=None):
        tags = []
        include_folder = None
        if filters:
            filters = [f.lower() for f in filters] # Transform into all lowercase

        for cur_el in soup.find_all():

            print('-'*10)
            prev_tag = cur_el.find_previous('h3')
            if prev_tag:
                prev_tag = prev_tag.contents[0].lower()

            if cur_el.name.lower() == 'h3':
                cur_tag = cur_el.contents[0].lower()
                if filters:
                    include_folder = (incl == True and cur_tag in filters) or \
                                     (incl == False and cur_tag not in filters)

                if not filters or include_folder:
                    tags.append(cur_tag)
                else:
                    continue

            elif cur_el.name.lower() == 'a':
                
                print("_RESOURCE_(A)_")
                print(cur_el.string)
                if include_folder or not filters:
                    add_res_to_db(cur_el, tags)


            elif cur_el.name.lower() == 'p' and tags \
                                            and cur_el.find_previous() \
                                            and (cur_el.find_previous().name == 'a' \
                                            or cur_el.find_previous().name == 'p') \
                                            and (prev_tag in tags):
                tags.pop()
                print("_TAGS_")
                print(tags)
                if not tags:
                    break
                
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

                incl = request.form.get('incl')
                excl = request.form.get('excl')

                if not incl and not excl: # Default import
                    search_and_insert()

                elif incl and not excl: # Include only
                    incl_items = incl.split(',')
                    search_and_insert(incl_items, incl=True)

                elif not incl and excl: # Exclude only
                    excl_items = excl.split(',')
                    search_and_insert(excl_items, incl=False)


                cur.close()
                conn.commit()
                flash('Resources imported successfully', 'success')

    return redirect(url_for('resources'))

# Export resources
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

    cur.execute(("""SELECT title, link, tags FROM resources WHERE user_id = %s ORDER BY tags"""),
    (user_id,)
    )

    user_resources = cur.fetchall()

    # Build relevant structure

    def_folder = Node(name="def", parent=None) # Tree Root
    def_folder.parent = None

    for res in user_resources:
        cur_res = classes.MixinResource(*res, res[0], 0, 0) # Set name same as title
        tags = res[2]

        if not tags:
            cur_res.parent = def_folder
            continue
        else:

            prev_folder = def_folder
            for idx,tag in enumerate(tags):

                # Check if folder/node already exists
                folder_exists = find(def_folder, lambda node: node.name == tag)
                if not folder_exists:
                    new_folder = Node(name=tag)

                    new_folder.parent = prev_folder # In the first iter this will be def_folder
                    prev_folder = new_folder
    
            # Add resource to the last Node/Folder
            cur_res.parent = find(def_folder, lambda node: node.name == tags[-1])
    print(RenderTree(def_folder, style=AsciiStyle()).by_attr())

    # Save text to byte object
    #strIO = BytesIO()
    #strIO.write(str.encode(final_text))
    #strIO.seek(0)

    # Send html file to client
    #return send_file(strIO, attachment_filename='3RStore_export.html', as_attachment=True)
