import json
from flask import Flask
import psycopg2 as pg
import os

app = Flask(__name__)
app.config.from_object(__name__)

dir_path = os.path.dirname(os.path.realpath(__file__))

# Read secret key from file
try:
    app.config['SECRET_KEY'] = open(os.path.join(dir_path,'seckey.txt'), 'rb').read()
    print("Read secret key succesfully")
except IOError:
    print("Error: No secret key.")


# Connect to PostgreSQL
# Read database properties for URI
DB_CONFIG = json.load(open(os.path.join(dir_path,'db.json'),'r'))
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
        tags VARCHAR(20)[1],
        date_of_posting TIMESTAMP NOT NULL,
        PRIMARY KEY (re_id)
        )""")

    cur.close()
    conn.commit()
except (Exception, pg.DatabaseError) as error:
    print("Unable to connect to the database" + error)

import _3RStore.views
