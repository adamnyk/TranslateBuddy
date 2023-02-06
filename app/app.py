from flask import Flask, render_template, url_for, session, redirect, flash, jsonify, g
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Translation, Phrasebook, PhrasebookTranslation
from forms import LoginForm, UserAddForm, TranslateForm, UserEditForm, PhrasebookForm
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
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', SESSION_KEY)
toolbar = DebugToolbarExtension(app)

connect_db(app)

translator = deepl.Translator(API_AUTH_KEY)
languages = [(l.code, l.name) for l in translator.get_target_languages()]


##############################################################################
# Translation functions

def get_translation(text, target_lang):
    """Fetches translation data from API and creates a new Translation object."""
    result = translator.translate_text(text, target_lang=target_lang)
    translation = Translation(lang_from=result.detected_source_lang,
                            lang_to=target_lang,
                            text_from=text,
                            text_to=result.text)
    
    return translation

##############################################################################
# User signup/login/logout

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None

def clear_translation():
    """Clear translation from session."""
    
    if "last_translation" in session:
        del session["last_translation"]
        
def check_login():
    """Check if user is logged in. If not redirect home and flash message."""
    if not g.user:
        flash("Access unauthorized.", "danger")
        return redirect("/")

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
        clear_translation()
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
            clear_translation()
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid login credentials.", 'danger')

    return redirect("/")


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    clear_translation()

    flash("You have successfully logged out.", 'success')
    return redirect("/")


####################################################################################
# Home Page

@app.route('/')
def home():
    login_form = LoginForm()
    register_form = UserAddForm()
    translate_form = TranslateForm(target_lang= session.get("lang") or "ES")
    translate_form.target_lang.choices = languages

    session['last_url'] = url_for('home')
    
    return render_template('home.html', login_form=login_form, register_form=register_form, translate_form=translate_form)

####################################################################################
# Translate Routes

@app.route('/translate', methods=["POST"])
def translate():
    """Fetch translation from API and create new translation object."""
    form = TranslateForm()
    form.target_lang.choices = languages
    


    if form.validate_on_submit():
        
        translation = get_translation(form.translate_text.data, form.target_lang.data)

        session["lang"] = translation.lang_to
        session["last_translation"] = translation.to_dict()

        return redirect(session["last_url"])
    
    flash("Translation did not submit", 'danger')
    return redirect(session["last_url"])


####################################################################################
# User Routes

@app.route('/user')
def show_user():
    """Show user profile and phrasebooks."""
    
    check_login()
    
    user_edit_form = UserEditForm()
    phrasebook_add_form = PhrasebookForm()
    clear_translation()
    session['last_url'] = url_for('show_user')

    return render_template("/user/profile.html", user_edit_form=user_edit_form, phrasebook_add_form=phrasebook_add_form)

@app.route('/user/edit', methods=["POST"])
def edit_user():
    """Edit user in db if user is logged in and confirms password. 
    If form is not valid, redirect home.
    If username is already taken: flash message and return to user page."""
    
    check_login()
    form = UserEditForm()
    user = g.user
    
    if form.validate_on_submit():
        if User.authenticate(user.username, form.password.data):
            try:
                user.username = form.username.data
                
                db.session.commit()
                
                return redirect("/user")
                
            except IntegrityError as e:
                flash("Username already taken", 'danger')
                return redirect("/user")
            
        flash("Wrong password, please try again.", 'danger')
    
    flash("User edit failed.", "danger")
    return redirect("/user")
    
    
@app.route('/user/delete', methods=["POST"])
def delete_user():
    """Delete user if user is logged in."""

    check_login()
    do_logout()

    g.user.delete()
    db.session.commit()

    flash(f"User {g.user.username} sucessfully deleted", "success")
    return redirect("/")


####################################################################################
# Phrasebook Routes

@app.route('/phrasebook/add', methods=["POST"])
def add_phrasebook():
    """If user is logged in, create a new phrasebook."""
    
    check_login()
    form = PhrasebookForm()

    
    if form.validate_on_submit():
        p = Phrasebook(name=form.name.data,
                       user_id=g.user.id,
                       public=form.public.data
                       )  
        db.session.add(p)
        db.session.commit()
        
        flash(f"Created phrasebook: {p.name}", "success")
        return redirect(session["last_url"])
    
    return redirect(session["last_url"])
    
@app.route('/phrasebook/<int:pb_id>/delete', methods=["POST"])
def delete_phrasebook(pb_id):
    """Delete phrasebook from database."""

    pb = Phrasebook.query.get_or_404(pb_id)
    pb.delete()
    db.session.commit()

    return redirect("/user")    



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