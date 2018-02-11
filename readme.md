# 3RStore
An application for storing links online.

## Status
This application is currently available [here](http://threerstore.herokuapp.com)

## Running it locally
Ooh boy here we go.

First of all you need [Python 3.x](https://www.python.org/downloads/)  
Then, go ahead and install PIP. Instructions for its installation are available [here](https://pip.pypa.io/en/stable/installing/)

To make sure all the depedencies are installed run:

    pip install -r requirements.txt


Since the project's file structure has changed, a simple 

    python __init__.py

will not suffice. 

### First way - Running the app with flask
First you need to set the environment variable for the application.

One way to do this is :

From /3RStore

On linux:

    export FLASK_APP=_3RStore/__init__.py

On windows:

    set FLASK_APP=_3RStore/__init__.py

Then (from this directory) simply run :

    flask run

to launch the server. A prompt indicating sucessfull launch should appear in the console.

If you want to set Flask's debug mode on you can use:

    export FLASK_DEBUG=true

And

    set FLASK_DEBUG=true

For Linux and Windows respectively.

Finally, you can open your browser and go to 

    http://127.0.0.1:5000/


### Second way - Running the app with waitress 

First run

    python server.py

Then go to 

    http://127.0.0.1:8080/

Ta-da!

## File Structure
<pre>
|   .gitignore
|   Procfile
|   readme.md
|   requirements.txt
|   server.py
|   setup.py
|   
\---_3RStore
    |   db.json
    |   errors.py
    |   forms.py
    |   seckey.txt
    |   views.py
    |   __init__.py
    |   
    +---static
    |   +---css
    |   |       resources.css
    |   |       
    |   +---icons
    |   |       3rlogo.png
    |   |       3rstore_logo.png
    |   |       android-chrome-192x192.png
    |   |       android-chrome-512x512.png
    |   |       apple-touch-icon.png
    |   |       browserconfig.xml
    |   |       favicon-16x16.png
    |   |       favicon-32x32.png
    |   |       favicon.ico
    |   |       manifest.json
    |   |       mstile-150x150.png
    |   |       safari-pinned-tab.svg
    |   |       
    |   \---js
    |           resources.js
    |           
    +---templates
    |   |   add_resource.html
    |   |   edit_resource.html
    |   |   error.html
    |   |   home.html
    |   |   layout.html
    |   |   login.html
    |   |   options.html
    |   |   register.html
    |   |   resources.html
    |   |   
    |   \---includes
    |           _formhelpers.html
    |           _messages.html
    |           _navbar.html
<pre>