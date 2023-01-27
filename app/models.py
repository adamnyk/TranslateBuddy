"""SQLAlchemy models for Translation Buddy"""

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy

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

    phrasebooks = db.relationship("Phrasebook", backref="user", passive_deletes="all")

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
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
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
        # passive_deletes="all",
    )

    def __repr__(self):
        return f"<Phrasebook #{self.id}: {self.name}>"


class PhrasebookTranslation(db.Model):
    """Mapping user phrasebooks to translations"""

    __tablename__ = "phrasebook_translation"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    phrasebook_id = db.Column(
        db.Integer,
        db.ForeignKey("phrasebooks.id", ondelete='CASCADE'),
    )

    translation_id = db.Column(
        db.Integer,
        db.ForeignKey("translations.id", ondelete='CASCADE'),
    )

    note = db.Column(db.Text)


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

    # note = db.Column(db.Text)
    
    def __repr__(self):
        return f"<Translation #{self.id}: {self.text_from} >> {self.text_to}>"


def connect_db(app):
    """Connect this database to provided Flask app."""

    db.app = app
    db.init_app(app)
