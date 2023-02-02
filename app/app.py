from flask import Flask, render_template, url_for, session, redirect, flash, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Translation, Phrasebook, PhrasebookTranslation
from forms import LoginForm, UserAddForm, TranslateForm
from sqlalchemy.exc import IntegrityError
import deepl
from secret import API_AUTH_KEY, SESSION_KEY

import os

CURR_USER_KEY = "curr_user"

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///translator-app'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', SESSION_KEY)
toolbar = DebugToolbarExtension(app)

connect_db(app)

translator = deepl.Translator(API_AUTH_KEY)
languages = [(l.code, l.name) for l in translator.get_target_languages()]


##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None


def do_login(user):
    """Log in user."""

    session[CURR_USER_KEY] = user.id


def do_logout():
    """Logout user."""

    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]


@app.route('/signup', methods=["POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    
    register_form = UserAddForm()
    login_form = LoginForm()
    
    if register_form.validate_on_submit():
        try:
            user = User.signup(
                username=register_form.username.data,
                password=register_form.password.data
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return redirect("/")

        do_login(user)
        flash("Welcome! Account created.", 'success')
        return redirect("/")

    flash("Reigistration failed!", 'danger')
            
    return render_template("home.html", register_form=register_form, login_form=login_form)


@app.route('/login', methods=["POST"])
def login():
    """Handle user login."""

    form = LoginForm()

    if form.validate_on_submit():
        user = User.authenticate(form.username.data,
                                 form.password.data)

        if user:
            do_login(user)
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid login credentials.", 'danger')

    return redirect("/")


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/")


####################################################################################
# Home Page

@app.route('/')
def home():
    login_form = LoginForm()
    register_form = UserAddForm()
    translate_form = TranslateForm(target_lang="ES")
    translate_form.target_lang.choices = languages


    
    return render_template('home.html', login_form=login_form, register_form=register_form, translate_form=translate_form)

####################################################################################
# User Routes

@app.route('/user/<int:user_id>')
def show_user(user_id):
    """Show user profile and phrasebooks."""
    
    return render_template("/user/profile.html")


######## 
# API demo
########

####### Translate
# result = translator.translate_text("Hello, wild one!", target_lang="FR")
# print(result.text)  # "Bonjour, le monde !"

####### Translate Document
# result = translator.translate_document_from_filepath(input_path="phrases.txt", output_path="result.txt", target_lang="FR")
# print(result.text)  # "Bonjour, le monde !"

###### Attempting to create cheet-sheet
# with open('phrases.txt') as f1, open('result.txt') as f2:
#     for l1, l2 in zip(f1,f2):
#         print(l1 + '          ' + l2)

###################################################################################