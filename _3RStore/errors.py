from _3RStore import app
from flask import render_template

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html',
                           ErrorCode='404',
                           ErrorMessage='Page not found. How did you even get here?'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('error.html',
                           ErrorCode='403',
                           ErrorMessage='Forbidden! Don\'t touch!'), 403

@app.errorhandler(410)
def gone(e):
    return render_template('error.html',
                           ErrorCode='410',
                           ErrorMessage='This page no longer exists.'), 410

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html',
                           ErrorCode='500',
                           ErrorMessage='Internal server error.'), 500
