from flask import session
import re as r

# Checks if a user is logged in
def logged_in(user_id=None):
    if user_id:
        return session.get('logged_in') and session['user_id'] == user_id
    else:
        return session.get('logged_in')

def list_contains_duplicates(data_list):
    if isinstance(data_list, list):
        return len(data_list) != len(set(data_list))
    else:
        return False

def characters_valid(data_string):
    return r.match(r"^[A-Za-z0-9_ \u0370-\u03ff\u1f00-\u1fff]*$", data_string)