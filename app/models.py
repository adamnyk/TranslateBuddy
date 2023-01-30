"""SQLAlchemy models for Translation Buddy"""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import auto_delete_orphans


bcrypt = Bcrypt()
db = SQLAlchemy()


class User(db.Model):
    """User in the system"""

    __tablename__ = "users"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    phrasebooks = db.relationship("Phrasebook", backref="user", cascade='all, delete-orphan')

    def __repr__(self):
        return f"<User #{self.id}: {self.username}>"

    @classmethod
    def signup(cls, username, password):
        """Sign up user.
        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode("UTF-8")

        user = User(username=username, password=hashed_pwd)

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
    @classmethod
    def delete(cls, user):
        """Detlete user and any orphaned translations."""
        translations = {t for pb in user.phrasebooks for t in pb.translations}
        
        db.session.delete(user)
        
        for t in translations:
            Translation.delete_orphan(t)


class Phrasebook(db.Model):
    """A user's saved collection of phrases."""

    __tablename__ = "phrasebooks"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    name = db.Column(
        db.String(),
        nullable=False,
    )

    user_id = db.Column(
        db.Integer, 
        db.ForeignKey("users.id"), 
        nullable=False
    )

    public = db.Column(
        db.Boolean,
        default=False,
        nullable=False,
    )

    translations = db.relationship(
        "Translation",
        secondary="phrasebook_translation",
        backref="phrasebooks",
    )

    def __repr__(self):
        return f"<Phrasebook #{self.id}: {self.name}>"
    
    @classmethod
    def delete(self, phrasebook):
        translations = phrasebook.translations
        db.session.delete(phrasebook)
        
        for t in translations:
            Translation.delete_orphan(t)
    
    @classmethod
    def delete_translation(self, translation, phrasebook):
        '''Delete phrasebook translation association and delete translation if orphaned.'''
        
        pt = PhrasebookTranslation.query.get((phrasebook.id, translation.id))
        db.session.delete(pt)
        
        Translation.delete_orphan(translation)


class PhrasebookTranslation(db.Model):
    """Mapping user phrasebooks to translations"""

    __tablename__ = "phrasebook_translation"

    # id = db.Column(
    #     db.Integer,
    #     primary_key=True
    # )

    phrasebook_id = db.Column(
        db.Integer,
        db.ForeignKey("phrasebooks.id"),
        primary_key=True
    )

    translation_id = db.Column(
        db.Integer,
        db.ForeignKey("translations.id"),
        primary_key=True
    )

    note = db.Column(db.Text)

    def __repr__(self):
        return f"<Phrasebook #{self.phrasebook_id}, Translation #{self.translation_id}>"


class Translation(db.Model):
    """Translations that have been saved by a user."""

    __tablename__ = "translations"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    lang_from = db.Column(
        db.String(),
        nullable=False,
    )

    lang_to = db.Column(
        db.String,
        nullable=False,
    )

    text_from = db.Column(
        db.Text,
        nullable=False,
    )

    text_to = db.Column(
        db.Text,
        nullable=False,
    )

    
    def __repr__(self):
        return f"<Translation #{self.id}: {self.text_from} >> {self.text_to}>"
    
    @classmethod
    def delete_orphan(self, translation):
        """Delete translation if it does not belong to any phrasebook."""
        if not len(translation.phrasebooks):
            db.session.delete(translation)
   

def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)
