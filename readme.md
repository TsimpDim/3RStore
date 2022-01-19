<img src="https://threerstore.herokuapp.com/static/icons/3rstore_logo.png" width="80px" height="80px">

An application for storing and managing links online.

## Status

This application is currently available [here](http://threerstore.herokuapp.com)

## Running it locally

Ooh boy here we go.

First of all you need [Python 3.x](https://www.python.org/downloads/)
Then, go ahead and install PIP. Instructions for its installation are available [here](https://pip.pypa.io/en/stable/installing/)

To make sure all the depedencies are installed run:

    pip install -r requirements.txt

Next, you must have a PostgreSQL database created. For that you can use [PG Admin](https://www.pgadmin.org/).

You will then have to create a `config.json` file which has the following structure:

```
{
    "DB":{
        "USER": <DB_USER>,
        "PWD": <DB_PASSWORD>,
        "HOST": <DB_HOST>,
        "DATABASE": <DB_NAME>,
        "PORT": <DB_PORT>
    },
    "SECRET_KEY": <your_scecret_key>,
    "MAIL_SERVER":"smtp.gmail.com",
    "MAIL_PORT":465,
    "MAIL_USE_TLS":false,
    "MAIL_USE_SSL":true,
    "MAIL_USERNAME": <EM_USER>,
    "MAIL_PASSWORD": <EM_PASSWORD>,
    "MAIL_DEFAULT_SENDER": <EM_USER>
}
```

- The `MAIL` settings/fields are necessary for the password recovery process, if you don't plant on using the feature you can remove them.

- The specified `MAIL_SERVER` and `MAIL_PORT` are for use with a GMAIL address.

- The `MAIL_DEFAULT_SENDER` property can be removed but then you will have to specify the `sender` when building a `Message`

---

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

_If you get an error regarding the build environment, set/export the `FLAK_ENV` variable to whatever you please_

---

### Second way - Running the app with waitress

First run

    python server.py

Then go to

    http://127.0.0.1:8080/

Ta-da!

## File Structure

<pre>
├── _3RStore
│   ├── static
│   │   ├── css
│   │   │   ├── deleted_resources.css
│   │   │   ├── _navbar.css
│   │   │   ├── options.css
│   │   │   ├── register.css
│   │   │   ├── resources_cmpct.css
│   │   │   └── resources.css
│   │   ├── icons
│   │   │   ├── 3rstore_logo.png
│   │   │   ├── android-chrome-192x192.png
│   │   │   ├── android-chrome-512x512.png
│   │   │   ├── apple-touch-icon.png
│   │   │   ├── browserconfig.xml
│   │   │   ├── favicon-16x16.png
│   │   │   ├── favicon-32x32.png
│   │   │   ├── favicon.ico
│   │   │   ├── mstile-150x150.png
│   │   │   ├── safari-pinned-tab.svg
│   │   │   └── site.webmanifest
│   │   └── js
│   │       ├── resources_cmpct.js
│   │       └── resources.js
│   ├── templates
│   │   ├── includes
│   │   │   ├── _formhelpers.html
│   │   │   ├── _messages.html
│   │   │   └── _navbar.html
│   │   ├── add_resource.html
│   │   ├── chng_password.html
│   │   ├── deleted_resources.html
│   │   ├── edit_resource.html
│   │   ├── email_pwd_reset.html
│   │   ├── error.html
│   │   ├── home.html
│   │   ├── layout.html
│   │   ├── login.html
│   │   ├── options.html
│   │   ├── register.html
│   │   ├── reset_password_start.html
│   │   ├── resources_cmpct.html
│   │   ├── resources_public.html
│   │   └── resources.html
│   ├── classes.py
│   ├── config.json
│   ├── errors.py
│   ├── forms.py
│   ├── __init__.py
│   └── views.py
├── .gitignore
├── Procfile
├── readme.md
├── requirements.txt
├── server.py
└── setup.py
<pre>
