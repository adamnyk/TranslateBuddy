"""Seed file to make sample data for translation-app db."""

from models import User, Translation, Phrasebook, PhrasebookTranslation
from app import db

# Create all tables
db.drop_all()
db.create_all()

# If table isn't empty, empty it
User.query.delete()

# Add users
adam = User(username="Adam", 
            password="password")

caro = User(username="Carolyn", 
            password="password")


db.session.add(adam)
db.session.add(caro)

db.session.commit()


# Add phrasebooks
Phrasebook.query.delete()

convo = Phrasebook(name="Conversation", user_id=1)
food = Phrasebook(name="Food", user_id=2)


db.session.add(convo)
db.session.add(food)

db.session.commit()


# Add translations
hello = Translation(lang_from='EN-US',
                    lang_to='ES',
                    text_from='Hello!',
                    text_to='Hola!'
                    )
cheese = Translation(lang_from='EN-US',
                    lang_to='ES',
                    text_from='cheese',
                    text_to='queso'
                    )

db.session.add(hello)
db.session.add(cheese)

db.session.commit()


# Add Phrasebook <> Translation connections

adam_hello = PhrasebookTranslation(phrasebook_id=1,
                                   translation_id=1)

caro_cheese = PhrasebookTranslation(phrasebook_id=2,
                                   translation_id=2)

db.session.add(adam_hello)
db.session.add(caro_cheese)

db.session.commit()
