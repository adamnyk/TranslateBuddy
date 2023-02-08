"""Seed file to make sample data for translation-app db."""

from models import User, Translation, Phrasebook, PhrasebookTranslation
from app import db

# Create all tables
db.drop_all()
db.create_all()

# If table isn't empty, empty it
User.query.delete()


# Add users
adamnyk = User(username="adamnyk",
               password="$2b$12$nL984KCxBMNZ9XgA9DrY4uz44S48e9x9kJRcqiszoxo.4xwRe2wpK")

carolynpc = User(username="carolynpc",
               password="$2b$12$PISmpjqI55l825D80j8Aterl5y2BzIaHbWnzUlBISLmnQfID5xCZy")

db.session.add(adamnyk)
db.session.add(carolynpc)

db.session.commit()

# Add phrasebooks
Phrasebook.query.delete()

food = Phrasebook(name="Food", user_id=1)
greetings = Phrasebook(name="Greetings", user_id=2)
convo = Phrasebook(name="Conversation", user_id=1)


db.session.add(food)
db.session.add(greetings)
db.session.add(convo)

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
que = Translation(lang_from='EN-US',
                    lang_to='ES',
                    text_from='what\'s up?',
                    text_to='¿Qué onda?'
                    )


db.session.add(hello)
db.session.add(cheese)
db.session.add(que)

db.session.commit()


# Add Phrasebook <> Translation connections

adam_hello = PhrasebookTranslation(phrasebook_id=1,
                                   translation_id=1,
                                   note="Adam's hello translation")

caro_hello = PhrasebookTranslation(phrasebook_id=2,
                                   translation_id=1,
                                    note="Caros's hello translation")

adam_cheese = PhrasebookTranslation(phrasebook_id=1,
                                   translation_id=2,
                                   note="Caro's cheese translation")
adam_que = PhrasebookTranslation(phrasebook_id=3,
                                   translation_id=3,
                                   note="Adam's que translation")

db.session.add(adam_hello)
db.session.add(caro_hello)
db.session.add(adam_cheese)
db.session.add(adam_que)

db.session.commit()
