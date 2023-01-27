"""Forms for Travel Translator"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField
from wtforms.validators import DataRequired, Length, EqualTo

class UserAddForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=6)])
    password = PasswordField('Password', validators=[Length(min=6)])
    password_confirm = PasswordField('Confirm Password', validators=EqualTo('password'))


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[Length(min=6)])