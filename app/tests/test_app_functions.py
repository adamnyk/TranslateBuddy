"""View tests"""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from flask import session
from models import db, User, Phrasebook, Translation, PhrasebookTranslation

os.environ["DATABASE_URL"] = "postgresql:///translator-test"


from app import app, CURR_USER_KEY, get_translation

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


with app.app_context():
    db.create_all()


class ViewsTestCase(TestCase):
    """Testing attributes of User model."""

    def setUp(self):
        """Create test client & mock data.
        2 users each with one phrasebook. User1 contains 2 translations. The first is only in user1's phrasebook, the 2nd is in both user1 and user2's phrasebooks"""

        db.drop_all()
        db.create_all()

        # create user 1
        u1 = User.signup("testuser", "password")
        uid1 = 111
        u1.id = uid1
        db.session.commit()

        u1 = User.query.get(uid1)
        self.u1 = u1
        self.uid1 = uid1

        # create user 2
        u2 = User.signup("testuser2", "password")
        uid2 = 222
        u2.id = uid2
        db.session.commit()

        u2 = User.query.get(uid2)
        self.u2 = u2
        self.uid2 = uid2

        # create a public phrasebook for user 1
        p1 = Phrasebook(
            name="phrasebook",
            user_id=self.uid1,
            public=True,
            lang_from="EN",
            lang_to="ES",
        )
        pid1 = 1
        p1.id = pid1
        db.session.add(p1)
        db.session.commit()

        p1 = Phrasebook.query.get(pid1)
        self.p1 = p1
        self.pid1 = pid1

        # create phrasebook for user 2
        p2 = Phrasebook(
            name="french phrases",
            user_id=self.uid2,
            public=False,
            lang_from="EN",
            lang_to="FR",
        )
        pid2 = 2
        p2.id = pid2
        db.session.add(p2)
        db.session.commit()

        p2 = Phrasebook.query.get(pid2)
        self.p2 = p2
        self.pid2 = pid2

        # Create translation and add to user 1's only phrasebook.
        t1 = Translation(
            lang_from="EN",
            lang_to="ES",
            text_from="What's going on, pumpkin?",
            text_to="¿Qué te pasa, calabaza?",
        )
        tid1 = 1
        t1.id = tid1
        db.session.add(t1)
        db.session.commit()

        t1 = Translation.query.get(tid1)
        self.t1 = t1
        self.tid1 = tid1

        self.p1.translations.append(t1)
        db.session.commit()

        # create second translation and add to user1's only phrasbook and user2's only phrasebook.
        t2 = Translation(
            lang_from="EN",
            lang_to="FR",
            text_from="What a test!",
            text_to="Quel test!",
        )
        tid2 = 2
        t2.id = tid2
        db.session.add(t2)
        db.session.commit()

        t2 = Translation.query.get(tid2)
        self.t2 = t2
        self.tid2 = tid2

        self.p1.translations.append(t2)
        self.p2.translations.append(t2)
        db.session.commit()

        p2_t2 = PhrasebookTranslation.query.get((pid2, tid2))
        p2_t2.note = "Tesing is happening! testuser2's testing note."
        db.session.commit()
        self.p2_t2 = p2_t2
        
        
        # create a third translation that belongs to no phrasebooks.
        t3 = Translation(
            lang_from="EN",
            lang_to="ES",
            text_from="I'm orphaned data",
            text_to="Soy datos huérfanos",
        )
        tid3 = 3
        t3.id = tid3
        db.session.add(t3)
        db.session.commit()

        t3 = Translation.query.get(tid3)
        self.t3 = t3
        self.tid3 = tid3

        db.session.commit()

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
        
    def test_get_translation(self):
        """Given text and languages, should return a valid translation object and translation into a target language"""
        translation = get_translation(text="hello world!", source_lang="EN", target_lang="ES")
        
        self.assertIsNotNone(translation)
        self.assertIsNone(translation.id)
        self.assertEqual(translation.text_from, "hello world!")
        self.assertEqual(translation.text_to, "¡Hola mundo!")
        self.assertEqual(translation.lang_from, "EN")
        self.assertEqual(translation.lang_to, "ES")
        self.assertIsInstance(translation, Translation)