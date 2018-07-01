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
from . import classes as cc
from anytree import Node, RenderTree, find, AsciiStyle, NodeMixin, AnyNode, PreOrderIter
import re as r

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
        try:
            cur.execute(("""
            SELECT * FROM users WHERE username = %s
            """), (username,))  # Comma for single element tuple
        except DatabaseError:
            cur.rollback()
            
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
                form.note.data = form.note.data.replace('</br>','\n') # Else the </br> tags will display as text

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

# Rename tag
@app.route("/renametag", methods=['POST'])
def renametag():

    tag = request.form.get('tag')
    replacement = request.form.get('replacement')

    if tag:
        cur = conn.cursor()
        cur.execute("UPDATE resources SET tags = array_replace(tags,%s,%s)",
        (tag, replacement)
        )

        cur.close()
        conn.commit()
    
    flash('Tag renamed successfully', 'success')
    return redirect(url_for('options'))

# Import resources
@app.route("/import_resources", methods=['GET', 'POST'])
def import_resources():
    cur = conn.cursor()

    def add_res_to_db(res:cc.BaseResource):

        # Transform tags to all lowercase
        tags = [tag.lower() for tag in res.tags]

        link = parse.unquote(res.link)

        if res.title:
            title = res.title[0:99]
        else:
            title = res.link[0:50] + '...'

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
        prev_was_res = False


        if filters:
            filters = [f.lower() for f in filters] # Transform into all lowercase

        for cur_el in soup.find_all():

            # Detect folders, aka <DT><H3> {folder name} </H3>
            if cur_el.name == 'h3':
                
                if prev_was_res and tags: 
                    tags.pop()
                tags.append(cur_el.string.lower())

            # Detect resources/links aka <DT><A {href}> {title} </A>
            if cur_el.name == 'a':
                new_resource = cc.BaseResource(cur_el.string, 
                                                cur_el.get('href'),
                                                tags)
                                    
                if (not incl and not filters) \
                or (incl and any(f in tags for f in filters)) \
                or (not incl and all(f not in tags for f in filters)):
                    add_res_to_db(new_resource)

                if not prev_was_res: prev_was_res = True

                
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

    def base_html():
        '''
        This function creates the following HTML structure:

            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <META CONTENT="text/html; charset=UTF-8" HTTP-EQUIV="Content-Type"></META>
            <TITLE>3RStore Resources</TITLE>
            <H1>3RStore</H1>
            <DL>
            <P TYPE="Main"></P>
            </DL><P></P>

        After the tag cleanup later on, what remains is the appropriate
        parsable form

            <!DOCTYPE NETSCAPE-Bookmark-file-1>
            <META CONTENT="text/html; charset=UTF-8" HTTP-EQUIV="Content-Type">
            <TITLE>3RStore Resources</TITLE>
            <H1>3RStore</H1>
            <DL><P TYPE="Main">
                {folder contents}
            </DL><P>
        '''

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

        return soup

    def new_bkmrk_folder(main_tag, folder_name, depth):
        '''
        This functions creates an HTML structure like so:

            
            <DT><H3> {folder name} </H3></DT>
            <DL><P></P>
            </DL><P></P>
        
        After the tag cleanup later on, what remains is the appropriate
        parsable form

            <DT><H3> {folder name} </H3>
            <DL><P>
            </DL><P>
        '''


        dt_tag = soup.new_tag('DT', ident=depth)
        h3_tag = soup.new_tag('H3', ident=depth)
        dl_tag = soup.new_tag('DL', ident=depth)
        p_tag = soup.new_tag('P', ident=depth)

        h3_tag.string = folder_name

        dt_tag.append(h3_tag)
        dl_tag.append(p_tag)

        main_tag.append(dt_tag)
        main_tag.append(dl_tag)
        main_tag.append(soup.new_tag('P', ident=depth)) # To close each folder we created

        return p_tag

    def new_bkmrk_link(main_tag, title, link, depth):
        ''' 
        This function creates an HTML structure like so:

            <DT><A {href = link}> {title} </A></DT>

        After the tag cleanup later on, what remains is the appropriate
        parsable form

            <DT><A {href = link}> {title} </A>

        '''

        dt_tag = soup.new_tag('DT', ident=depth)
        
        a_tag = soup.new_tag('A', ident=depth)
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

    for res in user_resources:
        # Build a new node for each resource
        cur_res = cc.MixinResource(res[0], res[1], res[2], res[0], 0, 0) # Set name same as title
        tags = res[2]

        # If a resource has no tags, put it in the root folder
        if not tags:
            cur_res.parent = def_folder
            continue
        else:

            # Build every subfolder of the resource
            # Which means creating a new node for every tag
            prev_folder = def_folder
            for tag in tags:

                # Check if folder/node already exists
                potential_folder = find(def_folder, lambda node: node.name == tag)
                if not potential_folder:
                    new_folder = Node(name=tag)
                    new_folder.parent = prev_folder # In the first iter this will be def_folder
                    prev_folder = new_folder
                else:
                    # So that despite not creating a new node the prev_folder
                    # Still holds the previous node/subfolder correctly
                    prev_folder = potential_folder
    
            # Add resource to the last Node/Folder
            cur_res.parent = find(def_folder, lambda node: node.name == tags[-1])
    
    # Handle the actual exporting
    soup = base_html()

    main_tag = soup.find('P', {'TYPE' : 'Main'})
    prev_folder = main_tag
    prev_was_res = False

    # Build the HTML string/file
    for node in PreOrderIter(def_folder):

        if type(node) == cc.MixinResource:
            new_bkmrk_link(prev_folder, node.title, node.link, (node.depth + 1))

            if not prev_was_res : prev_was_res = True
        else:
            if prev_was_res: prev_folder = main_tag

            prev_folder = new_bkmrk_folder(prev_folder, node.name, (node.depth + 1))
        
    # Remove unecessary tags and add newlines
    final_text = str(soup).replace('</META>', '\n').replace('</TITLE>', '</TITLE>\n') \
    .replace('</H1>', '</H1>\n').replace('<DT', '\n<DT').replace('<DL', '\n<DL') \
    .replace('</P>', '').replace('</DT>', '').replace('</DL><P', '\n</DL><P')

    # Add proper identation
    split_text = final_text.splitlines()
    for idx,line in enumerate(split_text):
        res = r.search(r'(?<=.ident=\")\d+', line)

        if res:
            tabs = int(res.group(0))
            split_text[idx] = '\t'*tabs + line
            
            # Remove the custom"ident" property
            split_text[idx] = r.sub(r' ident=\"\d+\"', '', split_text[idx]) 
    
    final_text = '\n'.join(split_text)

    # Save text to byte object
    strIO = BytesIO()
    strIO.write(str.encode(final_text))
    strIO.seek(0)

    # Send html file to client
    return send_file(strIO, attachment_filename='3RStore_export.html', as_attachment=True)
