from flask import session

# Checks if a user is logged in
def logged_in(user_id=None):
    if user_id:
        return session.get('logged_in') and session['user_id'] == user_id
    else:
        return session.get('logged_in')