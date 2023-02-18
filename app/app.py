from flask import Flask, render_template, url_for, session, redirect, flash, jsonify, g, request
from flask_debugtoolbar import DebugToolbarExtension
from models import db, connect_db, User, Translation, Phrasebook, PhrasebookTranslation
from forms import LoginForm, UserAddForm, TranslateForm, UserEditForm, PhrasebookForm, AddTranslationForm, NoteForm, EditPhrasebookForm, FilterPhrasebookFrom
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


source_languages = [(l.code, l.name) for l in translator.get_source_languages()]
target_languages = [(l.code, l.name) for l in translator.get_target_languages()]


##############################################################################
# Translation functions

def get_translation(text, source_lang, target_lang):
    """Fetches translation data from API and creates a new Translation object."""
    result = translator.translate_text(text, source_lang=source_lang, target_lang=target_lang)
    translation = Translation(lang_from=source_lang,
                            lang_to=target_lang,
                            text_from=text,
                            text_to=result.text)
    
    return translation

##############################################################################
# Before request

@app.before_request
def add_user_to_g():
    """If we're logged in, add curr user to Flask global."""

    if CURR_USER_KEY in session:
        g.user = User.query.get(session[CURR_USER_KEY])

    else:
        g.user = None
        
@app.before_request
def add_langs_to_g():
    """If user is logged in, put language codes and names in Flask global"""
   
    if CURR_USER_KEY in session:
        g.langs = source_languages
        
@app.before_request
def set_default_sort():
    """Set default phrasebook sorting method to id if not set by user.
    Otherwise user and public phrasebooks will return an error.""" 
   
    if "sort" not in session:
        session["sort"] = "id"
        
    if "sort_public" not in session:
        session["sort_public"] = "id"


##############################################################################
# User signup/login/logout
def clear_translation():
    """Clear translation from session."""
    
    if "last_translation" in session:
        del session["last_translation"]
        
def reset_sort():
    """Reset phrasebook sort settings to default""" 
    session["sort"] = "id"
    session["sort_public"] = "id"
        
def reset_filter():
    """Reset filter if user navigates away from page. """

    if request.path == "/user":
        if 'filter' in session and request.referrer != request.url: 
            del session['filter']
        
    if request.path == "/public":  
        if 'filter_public_from' in session and request.referrer != request.url: 
            del session['filter_public_from']
        if 'filter_public_to' in session and request.referrer != request.url: 
            del session['filter_public_to']
        
        
def find_existing_translation(translation):
    """Given a translation, find an existing translation with the same information.
    If translation exists, return it, otherwise return None."""
        
    found = Translation.query.filter_by(
        text_from=translation.text_from, 
        text_to=translation.text_to, 
        lang_to=translation.lang_to).first()
    
    if found:
        return found
    return False
        
def unauthorized():
    """Check if user is logged in. If not redirect home and flash message."""
        
    flash("Access unauthorized.", "danger")
    return redirect("/")


##############################################################################
# User signup/login/logout
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
            flash(f"Hello, {user.username}!", "success")
            return redirect("/")

        flash("Invalid login credentials.", 'danger')

    return redirect("/")


@app.route('/logout')
def logout():
    """Handle logout of user."""

    do_logout()
    clear_translation()
    reset_sort()


    flash("You have successfully logged out.", 'success')
    return redirect("/")


####################################################################################
# Home Page

@app.route('/')
def home():


    login_form = LoginForm()
    register_form = UserAddForm()
    
    phrasebook_add_form = PhrasebookForm(lang_from = session.get("lang_from") or "EN", 
                                         lang_to = session.get("lang_to") or "ES",)
    phrasebook_add_form.lang_from.choices = source_languages
    phrasebook_add_form.lang_to.choices = source_languages
    
    translate_form = TranslateForm(source_lang = session.get("lang_from") or "EN",
                                   target_lang = session.get("lang_to") or "ES")
    translate_form.target_lang.choices = target_languages
    translate_form.source_lang.choices = source_languages
    
    save_translation_form = AddTranslationForm()
    
    
    if g.user:
        save_translation_form.phrasebooks.choices = [(p.id, p.name) for p in g.user.phrasebooks]
        

    
    return render_template('home.html', login_form=login_form, register_form=register_form, translate_form=translate_form, save_translation_form=save_translation_form, phrasebook_add_form=phrasebook_add_form)

####################################################################################
# Translate Routes

@app.route('/translate', methods=["POST"])
def translate():
    """Fetch translation from API and create new translation object."""
    form = TranslateForm()
    form.source_lang.choices = source_languages
    form.target_lang.choices = target_languages




    if form.validate_on_submit():
        
        translation = get_translation(form.translate_text.data, 
                                      form.source_lang.data, 
                                      form.target_lang.data)

        session["lang_from"] = form.source_lang.data
        session["lang_to"] = translation.lang_to
        session["last_translation"] = translation.to_dict()

        return redirect("/")
    
    flash("Translation did not submit", 'danger')
    return redirect("/")


####################################################################################
# User Routes


@app.route('/user')
def show_user():
    """Show user profile and phrasebooks."""


    if not g.user: return unauthorized()
    
    clear_translation()
    reset_filter()
    
    user_edit_form = UserEditForm(username=g.user.username)
    
    phrasebook_add_form = PhrasebookForm(lang_from = session.get("lang_from") or "EN", 
                                         lang_to = session.get("lang_to") or "ES",)
    phrasebook_add_form.lang_from.choices = source_languages
    phrasebook_add_form.lang_to.choices = source_languages
    
    pb_edit_form = EditPhrasebookForm()
    
    note_form = NoteForm()
    
    pb_langs = {pb.lang_to for pb in g.user.phrasebooks}

    return render_template("/user/profile.html", user_edit_form=user_edit_form, phrasebook_add_form=phrasebook_add_form, pb_edit_form=pb_edit_form, note_form=note_form, pb_langs=pb_langs)

@app.route('/user/edit', methods=["POST"])
def edit_user():
    """Edit user in db if user is logged in and confirms password. 
    If form is not valid, redirect home.
    If username is already taken: flash message and return to user page."""
    
    if not g.user: return unauthorized()
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

    if not g.user: return unauthorized()
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
    
    if not g.user: return unauthorized()

    form = PhrasebookForm()

    form.lang_from.choices = source_languages
    form.lang_to.choices = source_languages
    
    if form.validate_on_submit():
        p = Phrasebook(name=form.name.data,
                       user_id=g.user.id,
                       lang_from=form.lang_from.data,
                       lang_to=form.lang_to.data,
                       public=form.public.data
                       )  
        db.session.add(p)
        db.session.commit()
        
        flash(f"Created phrasebook: {p.name}", "success")
        return redirect(request.referrer)
    
    return redirect(request.referrer)

@app.route('/phrasebook/<int:pb_id>/edit', methods=["POST"])
def edit_phrasebook(pb_id):
    """Edit phrasebook in database."""

    if not g.user: return unauthorized()
    
    form = EditPhrasebookForm()
    
    if form.validate_on_submit():
        pb = Phrasebook.query.get_or_404(pb_id)
        pb.name = form.name.data
        pb.public = form.public.data
        
        db.session.commit()
        
        flash(f"Phrasebook updated.", "success")
        return redirect("/user")
    
    flash("Phrasebook edit unsuccessful.", "danger")
    return redirect("/user")
    
@app.route('/phrasebook/<int:pb_id>/delete', methods=["POST"])
def delete_phrasebook(pb_id):
    """Delete phrasebook from database."""

    if not g.user: return unauthorized()
    pb = Phrasebook.query.get_or_404(pb_id)
    pb.delete()
    db.session.commit()

    return redirect("/user")   

####################################################################################
# Public Phrasebook Routes

@app.route('/public')
def show_public_phrasebooks():
    """Show public phrasebooks from all users."""


    if not g.user: return unauthorized()
    reset_filter()
         
    save_translation_form = AddTranslationForm()
    save_translation_form.phrasebooks.choices = [(p.id, p.name) for p in g.user.phrasebooks]
    
    public_pbs = Phrasebook.query.filter(Phrasebook.public==True, 
                                         Phrasebook.user_id!=g.user.id).all()

    # Creating sets of languages for use in phrasebook filter. 
    codes_from = list({pb.lang_from for pb in public_pbs})
    codes_to = list({pb.lang_to for pb in public_pbs})
    
    choices_from = [(x,y) for x,y in source_languages if x in codes_from]
    choices_to = [(x,y) for x,y in source_languages if x in codes_to]
    
    
    filter_form = FilterPhrasebookFrom()
    filter_form.lang_from.choices = choices_from
    filter_form.lang_to.choices = choices_to
    
    if 'filter_public_from' and "filter_public_to" in session:
        public_pbs = Phrasebook.query.filter_by(public=True,
                                            lang_from=session['filter_public_from'],
                                            lang_to=session['filter_public_to'])
        

    return render_template("show_public.html", public_pbs=public_pbs, save_translation_form=save_translation_form, filter_form=filter_form)

@app.route('/public/translation/<int:t_id>/add', methods=["POST"])
def add_public_translation(t_id):
    """Add translation from a public phrasebooks to a user's phrasebook"""
    
    if not g.user: return unauthorized()
    
    form = AddTranslationForm()
    form.phrasebooks.choices = [(p.id, p.name) for p in g.user.phrasebooks]
    
    if not form.phrasebooks.data:
        flash("No data submitted", "danger")
        return redirect("/public")
    
    if form.validate_on_submit():
        t = Translation.query.get_or_404(t_id)

        for pb_id in form.phrasebooks.data:
            pb = Phrasebook.query.get(pb_id)
            pb.translations.append(t)
            db.session.commit()

        flash(f"Translation saved to {pb.name}", "success")
        return redirect("/public")
    
    
@app.route('/public/phrasebook/<int:pb_id>/add', methods=["POST"])
def add_public_phrasebook(pb_id):
    """Copy a public phrasebook to the current user's profile."""
    
    if not g.user: return unauthorized()
    
    pb = pb = Phrasebook.query.get_or_404(pb_id)
    
    new_pb = Phrasebook(name = pb.name,
                        user_id = g.user.id,
                        lang_from = pb.lang_from,
                        lang_to = pb.lang_to)
    
    for t in pb.translations:
        new_pb.translations.append(t)
        
    db.session.add(new_pb)
    db.session.commit()
    
    flash(f"Phrasebook {pb.name} copied successfully.", "success")
    return redirect("/public")

####################################################################################
# Sort / Filter Phrasebook Routes

@app.route('/sort/<sort_by>')
def sort_phrasebook(sort_by):
    """Sort phrasebooks by field indicated by adjusting session."""
    
    if request.referrer.endswith("/user"):
        session['sort']=sort_by
        return redirect(request.referrer)

    if request.referrer.endswith("/public"):
        session['sort_public']=sort_by
        return redirect(request.referrer)

@app.route('/filter/<lang_code>')
def filter_phrasebook(lang_code):
    """Filter user phrasebooks by language code."""
    
    if lang_code == "all":
        if 'filter' in session: session.pop('filter') 
        return redirect(request.referrer)
    else:
        session['filter'] = lang_code
        return redirect(request.referrer)      
    
@app.route('/filter', methods=['GET', 'POST']) 
def filter_public_phrasebook():
    '''Handle public phrasebook filter form and set filter settings in session.
    If accessed as a get request, show all public phrasebooks. If form is submitted, filter by language.'''

    if not g.user: return unauthorized()

    if request.method == 'GET':
        if 'filter_public_from' in session: session.pop('filter_public_from')
        if 'filter_public_to' in session: session.pop('filter_public_to')
        return redirect(request.referrer)
        

    public_pbs = Phrasebook.query.filter_by(public=True).all()

    # Creating sets of languages for use in phrasebook filter. 
    codes_from = list({pb.lang_from for pb in public_pbs})
    codes_to = list({pb.lang_to for pb in public_pbs})
    
    choices_from = [(x,y) for x,y in source_languages if x in codes_from]
    choices_to = [(x,y) for x,y in source_languages if x in codes_to]
    
    form = FilterPhrasebookFrom()
    form.lang_from.choices = choices_from
    form.lang_to.choices = choices_to

    if form.validate_on_submit():

        session['filter_public_from'] = form.lang_from.data
        session['filter_public_to'] = form.lang_to.data
        
        flash(f"Filter applied.  {form.lang_from.data} -> {form.lang_to.data}", "success")
    else:
        flash("sort failed.", "danger")
    
    return redirect(request.referrer)


####################################################################################
# Translation Routes

@app.route('/translation/add', methods=["POST"])
def add_translation():
    """Add translation to database and add association to one or more phrasebooks."""
    
    if not g.user: return unauthorized()
    
    form = AddTranslationForm()
    form.phrasebooks.choices = [(p.id, p.name) for p in g.user.phrasebooks]

    if not form.phrasebooks.data:
        flash("No data submitted", "danger")
        return redirect("/")
    
    if form.validate_on_submit:
        new_translation = Translation(**session["last_translation"])
        
        if  not find_existing_translation(new_translation):
            db.session.add(new_translation)
            db.session.commit()        
        else:    
            new_translation = find_existing_translation(new_translation)

        for pb_id in form.phrasebooks.data:
            pb = Phrasebook.query.get(pb_id)
            pb.translations.append(new_translation)
            db.session.commit()

        flash(f"Translation saved to {pb.name}", "success")
        return redirect(request.referrer)
    
    else:
        flash("Form did not validate.", "danger")
        return redirect("/")


@app.route('/<int:pb_id>/<int:t_id>/note', methods=["POST"])
def edit_translation_note(pb_id, t_id):
    """Edit note on user's translation (on association)"""
    
    if not g.user: return unauthorized()
    form = NoteForm()
    
    if form.validate_on_submit():
        pb_t = PhrasebookTranslation.query.get((pb_id, t_id))
        pb_t.note = form.note.data
    
        db.session.commit()
        return redirect(request.referrer)
    
    flash("Note submission failed.", "danger")
    return redirect(request.referrer)


@app.route('/phrasebook/<int:pb_id>/translation/<int:t_id>/delete', methods=["POST"])
def delete_translation(pb_id, t_id):
    """Delete translation from phrasebook and its association in database.
    Check if translation is orphaned, and if so, delete it from the database."""
    
    if not g.user: return unauthorized()
    pb = Phrasebook.query.get_or_404(pb_id)
    t = Translation.query.get_or_404(t_id)
    pb.delete_translation(t)
    db.session.commit()
    
    flash("Translation deleted.", "warning")
    return redirect(request.referrer)






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