"""Forms for Travel Translator"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo


class UserAddForm(FlaskForm):
    """User registration form."""

    username = StringField("Username", validators=[DataRequired(), Length(min=6)])
    password = PasswordField("Password", validators=[Length(min=6)])
    password_confirm = PasswordField(
        "Confirm Password", validators=[EqualTo("password")]
    )


class UserEditForm(FlaskForm):
    """User edit from."""

    username = StringField("New username", validators=[DataRequired()])
    password = PasswordField("Confirm password", validators=[Length(min=6)])


class LoginForm(FlaskForm):
    """Login form."""

    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[Length(min=6)])


class TranslateForm(FlaskForm):
    """Text translation form."""

    translate_text = TextAreaField("Text to translate", validators=[Length(max=100), DataRequired()])
    target_lang = SelectField("Translate into:", validators=[DataRequired()])


class PhrasebookForm(FlaskForm):
    """New phrasebook form."""
    
    name = StringField("Name", validators=[DataRequired(), Length(max=35)])
    public = BooleanField("Make public?")
    
    
class SaveTranslationForm(FlaskForm):
    """Save translation to user phrasebook."""
    
    
class NoteForm(FlaskForm):
    """Add / edit user's translation note."""
    
    note = TextAreaField("Note")


