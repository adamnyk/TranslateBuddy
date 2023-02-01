from flask import Flask, render_template, url_for, session, redirect, flash, jsonify, g
from models import db, connect_db, User, Translation, Phrasebook, PhrasebookTranslation
from forms import LoginForm, UserAddForm
from sqlalchemy.exc import IntegrityError
import deepl
from secret import API_AUTH_KEY, SESSION_KEY

import os

CURR_USER_KEY = None

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = (
    os.environ.get('DATABASE_URL', 'postgresql:///translator-app'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ECHO'] = False
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = True
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', SESSION_KEY)

connect_db(app)

translator = deepl.Translator(API_AUTH_KEY)
languages = [l.name for l in translator.get_target_languages()]


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


@app.route('/signup', methods=["GET", "POST"])
def signup():
    """Handle user signup.
    Create new user and add to DB. Redirect to home page.
    If form not valid, present form.
    If the there already is a user with that username: flash message
    and re-present form.
    """
    if CURR_USER_KEY in session:
        del session[CURR_USER_KEY]
    form = UserAddForm()

    if form.validate_on_submit():
        try:
            user = User.signup(
                username=form.username.data,
                password=form.password.data,
                email=form.email.data,
                image_url=form.image_url.data or User.image_url.default.arg,
            )
            db.session.commit()

        except IntegrityError as e:
            flash("Username already taken", 'danger')
            return render_template('users/signup.html', form=form)

        do_login(user)

        return redirect("/")

    else:
        return render_template('users/signup.html', form=form)


@app.route('/login', methods=["GET", "POST"])
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

        flash("Invalid credentials.", 'danger')

    return render_template('users/login.html', form=form)


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()

    flash("You have successfully logged out.", 'success')
    return redirect("/login")


####################################################################################
# Home Page

@app.route('/')
def home():
    login_form = LoginForm()
    register_form = UserAddForm()

    
    return render_template('home.html', login_form=login_form, register_form=register_form)

####################################################################################




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