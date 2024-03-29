from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from _3RStore import conn
from . import helpers
import re as r


class ResourceForm(Form):
    """Resource form class. Gets input for title,link,note and tags and validates it."""

    title = StringField(
        "Title", [validators.DataRequired(), validators.Length(min=1, max=100)]
    )
    link = StringField("Link", [validators.DataRequired(), validators.URL()])
    note = TextAreaField("Note")
    tags = StringField("Tags")

    def validate(self):

        # Validate as is and then go ahead with the other checks
        validation = Form.validate(self)
        if not validation:
            return False

        tags_list = self.tags.data.split(",")

        # If user has entered no tags
        if not tags_list or (tags_list and tags_list[0] == ""):
            return True

        # If list contains duplicate values (the same tag many times)
        if helpers.list_contains_duplicates(tags_list):
            self.tags.errors.append("Duplicate tags are not allowed.")
            return False

        # Invalid characters
        if helpers.characters_valid(self.tags.data):
            return True
        else:
            self.tags.errors.append("Invalid characters were given.")
            return False

        # Misc
        for tag in tags_list:
            if len(tag) > 20:
                self.tags.errors.append(
                    "Each tag cannot be more than 20 characters. Seperate tags with a comma."
                )
                return False

            if "-" in tag:
                self.tags.errors.append("Character '-' is not allowed in tags.")
                return False

            if not tag:
                self.tags.errors.append("Empty tags are not allowed.")
                return False
        return True


# Register Form Class
class RegisterForm(Form):
    """Register Form Class. Gets input for username,email,and password and validates it"""

    username = StringField(
        "Username", [validators.DataRequired(), validators.Length(min=5, max=45)]
    )
    email = StringField(
        "Email",
        [
            validators.DataRequired(),
            validators.Length(min=8, max=50),
            validators.Email(),
        ],
    )
    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Passwords do not match."),
            validators.Length(min=8),
        ],
    )

    confirm = PasswordField("Confirm Password")

    def validate(self):

        # Validate as is and then go ahead with the other checks
        validation = Form.validate(self)
        if not validation:
            return False

        cur = conn.cursor()

        # If username exists
        cur.execute(
            "SELECT username FROM users WHERE username=%s", (self.username.data,)
        )

        exists = cur.fetchall()

        if exists:
            self.username.errors.append("Username already exists.")
            return False

        # If email exists
        cur.execute("SELECT email FROM users WHERE email=%s", (self.email.data,))

        exists = cur.fetchall()

        if exists:
            self.email.errors.append("Email is already registered.")
            return False
        return True


# Change password Form Class
class ChangePassForm(Form):

    password = PasswordField(
        "Password",
        [
            validators.DataRequired(),
            validators.EqualTo("confirm", message="Passwords do not match."),
            validators.Length(min=8),
        ],
    )

    confirm = PasswordField("Confirm Password")


# Recover password Form Class
class EmailForm(Form):
    email = StringField(
        "Email", validators=[validators.DataRequired(), validators.Email()]
    )

    def validate(self):
        validation = Form.validate(self)
        if not validation:
            return False

        cur = conn.cursor()

        # If email exists
        cur.execute("SELECT email FROM users WHERE email=%s", (self.email.data,))

        exists = cur.fetchall()

        if not exists:
            self.email.errors.append("Invalid email address.")
            return False
        return True
