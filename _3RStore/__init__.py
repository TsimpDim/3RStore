import json
import os
from flask import Flask, request
from flask_mail import Mail
from flask_cors import CORS
import psycopg2 as pg
from flask_sslify import SSLify

app = Flask(__name__)
dir_path = os.path.dirname(os.path.realpath(__file__))

config_name = "config.json"
if os.environ.get("LOCAL_EXEC"):
    config_name = "config_local.json"

CONFIG = json.load(open(os.path.join(dir_path, config_name), 'r'))


# Add Access-Control-Allow-Origin Header
CORS(app, resources={r"/*": {"origins": "https://threerstore.herokuapp.com"}})

# Add Common Security HTTP Headers
@app.after_request
def addCommonHeaders(response):
    # Changes the server name to something else other than the default one
    response.headers['Server'] = '3R Store WS'

    # Adds a touch of humor
    response.headers['X-Hello-Human'] = 'Hi there human, my good old friend.'

    # Prevents external sites from embedding your site in an iframe
    response.headers["X-Frame-Options"] = 'SAMEORIGIN'

    # The browser will try to prevent reflected XSS attacks
    response.headers['X-XSS-Protection'] = '1; mode=block'

    # Tells the browser to convert all HTTP requests to HTTPS, preventing man-in-the-middle (MITM) attacks.
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

    # Forces the browser to honor the response content type instead of trying to detect it
    response.headers['X-Content-Type-Options'] = 'nosniff'

    # Tell the browser where it can load various types of resource from
    response.headers['Content-Security-Policy'] = 'default-src \'self\' \'unsafe-inline\' https://stackpath.bootstrapcdn.com/bootstrap/ https://maxcdn.bootstrapcdn.com/font-awesome/ https://code.jquery.com https://npmcdn.com https://cdnjs.cloudflare.com/ajax/libs/popper.js/' 
    return response

app.config.from_object(__name__)
app.config.update(CONFIG)

mail = Mail(app)

if os.environ.get('DYNO'): # Only serve over HTTPS on Heroku
    app.config.update(
        SESSION_COOKIE_SECURE = True,
        REMEMBER_COOKIE_SECURE = True,
        SESSION_COOKIE_HTTPONLY = True,
        REMEMBER_COOKIE_HTTPONLY = True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    sslify = SSLify(app, subdomains=True, permanent=True)


# Connect to PostgreSQL
# Read database properties for URI
USER = CONFIG['DB']['USER']
PASSWORD = CONFIG['DB']['PWD']
HOST = CONFIG['DB']['HOST']
NAME = CONFIG['DB']['DATABASE']
PORT = CONFIG['DB']['PORT']

conn = None  # Declared here so we can use it later
try:
    print("Connecting to database...")

    conn = pg.connect(("dbname={} user={} host={} password={} port={}").format(
        NAME, USER, HOST, PASSWORD, PORT))
    cur = conn.cursor()
    cur.execute(
        """CREATE TABLE IF NOT EXISTS users (
        id SERIAL,
        email VARCHAR(50) NOT NULL,
        username VARCHAR(45) NOT NULL,
        password VARCHAR(100) NOT NULL,
        date_of_reg TIMESTAMP NOT NULL,
        PRIMARY KEY (id)
        )""")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS resources (
        re_id SERIAL,
        user_id INT NOT NULL REFERENCES users(id),
        title VARCHAR(100) NOT NULL,
        link TEXT NOT NULL,
        note TEXT,
        tags VARCHAR(40)[1],
        date_of_posting TIMESTAMP NOT NULL,
        PRIMARY KEY (re_id)
        )""")

    cur.execute(
        """CREATE TABLE IF NOT EXISTS trash (
        re_id SERIAL,
        user_id INT NOT NULL REFERENCES users(id),
        title VARCHAR(100) NOT NULL,
        link TEXT NOT NULL,
        note TEXT,
        tags VARCHAR(40)[1],
        date_of_posting TIMESTAMP NOT NULL,
        PRIMARY KEY (re_id)
        )""")

    cur.close()
    conn.commit()
except (Exception, pg.DatabaseError) as error:
    print("Unable to connect to the database")
    raise error

print("Connected to database successfully.")

import _3RStore.views
import _3RStore.errors
