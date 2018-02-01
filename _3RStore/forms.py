from wtforms import Form, StringField, TextAreaField, PasswordField, validators


class ResourceForm(Form):
    '''Resource form class. Gets input for title,link,note and tags and validates it.'''

    title = StringField('Title', [
        validators.DataRequired(),
        validators.Length(min=1, max=100)
    ])
    link = StringField('Link', [
        validators.DataRequired(),
        validators.URL()
    ])
    note = TextAreaField('Note')
    tags = StringField('Tags')

    def validate(self):

        validation = Form.validate(self)
        if not validation:
            return False

        tags_list = self.tags.data.split(',')
        # If user has entered no tags
        if not tags_list or (tags_list and tags_list[0] == ''):
            return True

        # If list contains duplicate values (the same tag many times)
        if len(tags_list) != len(set(tags_list)):
            self.tags.errors.append('Duplicate tags are not allowed.')
            return False

        for tag in tags_list:
            if len(tag) > 20:
                self.tags.errors.append(
                    'Each tag cannot be more than 20 characters. Seperate tags with a comma.')
                return False

            if not tag:
                self.tags.errors.append('Empty tags are not allowed.')
                return False
        return True


# Register Form Class
class RegisterForm(Form):
    '''Register Form Class. Gets input for username,email,and password and validates it'''

    username = StringField('Username', [
        validators.DataRequired(),
        validators.Length(min=5, max=45)
    ])
    email = StringField('Email', [
        validators.DataRequired(),
        validators.Length(min=8, max=50),
        validators.Email()
    ])
    password = PasswordField('Password', [
        validators.DataRequired(),
        validators.EqualTo('confirm', message='Passwords do not match')
    ])

    confirm = PasswordField('Confirm Password')
