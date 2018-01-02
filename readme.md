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

will not suffice. First you need to set the environment variable for the application.

One way to do this is :

Navigate to 3RStore/_3RStore 

On linux:

    export FLASK_APP = __init__.py

On windows:

    set FLASK_APP = __init__.py

Then (from this directory) simply run :

    flask run


to launch the server. A prompt indicating sucessfull launch should appear in the console.

Finally, open your browser and go to 

    http://127.0.0.1:5000/

Ta-da!

## File Structure
<pre>
|   .gitignore
|   readme.md
|   requirements.txt
|   setup.py
|   
\---_3RStore
    |   db.json
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
    \---templates
        |   add_resource.html
        |   edit_resource.html
        |   home.html
        |   layout.html
        |   login.html
        |   register.html
        |   resources.html
        |   
        \---includes
                _formhelpers.html
                _messages.html
                _navbar.html
<pre>