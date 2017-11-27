import os
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash


app = Flask(__name__)
app.config.from_object(__name__) # load config from this file , flaskr.py

# Load default config and override config from an environment variable

@app.route('/')
def index():
    return render_template('home.html')

if __name__ == '__main__':
    app.run(debug=True)