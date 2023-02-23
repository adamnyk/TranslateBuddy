"""Translate views tests"""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc
from flask import session
from models import db, User, Phrasebook, Translation, PhrasebookTranslation
from bs4 import BeautifulSoup

os.environ["DATABASE_URL"] = "postgresql:///translator-test"


from app import app, CURR_USER_KEY

app.config['WTF_CSRF_ENABLED'] = False
app.config['TESTING'] = True
app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


with app.app_context():
    db.create_all()


class ViewsTestCase(TestCase):
    """Testing app view functions."""

    def setUp(self):
        """Create test client & mock data.
        2 users each with one phrasebook. User1 contains 2 translations. The first is only in user1's phrasebook, the 2nd is in both user1 and user2's phrasebooks"""


        db.drop_all()
        db.create_all()
        
        self.client = app.test_client()

        # create user 1
        u1 = User.signup("testuser", "password")
        uid1 = 111
        u1.id = uid1
        db.session.commit()

        u1 = User.query.get(uid1)
        self.u1 = u1
        self.uid1 = uid1



    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()


##################################################
# Translate tests
##################################################

    def test_translate_logged_out(self):
        """Does translate route return a correct result and put translation data into flask session. Add-translation and add-phrasebok forms should not be present on page."""
        with self.client as c:
            
            resp = c.post("/translate", data={
                "translate_text": "hello world!",
                "source_lang": "EN",
                "target_lang": "ES"
            }, follow_redirects=True)

            html = resp.get_data(as_text=True)

            self.assertEqual(resp.status_code, 200)
            self.assertIn("RESULT:", html)
            self.assertIn("¡Hola mundo!", html)
            self.assertNotIn('translation/add', html)
            self.assertNotIn('phrasebook/add', html)
            self.assertEqual(session['lang_from'], "EN")
            self.assertEqual(session['lang_to'], "ES")
            self.assertIsNotNone(session['last_translation'])
            self.assertEqual(session['last_translation']['text_from'], "hello world!")
            self.assertEqual(session['last_translation']['text_to'], "¡Hola mundo!")
            self.assertEqual(session['last_translation']['lang_from'], "EN")
            self.assertEqual(session['last_translation']['lang_to'], "ES")
            self.assertIsNone(session['last_translation']['id'])

            
    def test_translate_logged_in(self):
            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = self.uid1
                
                resp = c.post("/translate", 
                              data={"translate_text": "hello world!",
                                    "source_lang": "EN",
                                    "target_lang": "ES"}, 
                              follow_redirects=True)
                

                html = resp.get_data(as_text=True)

                self.assertEqual(resp.status_code, 200)
                self.assertIn("RESULT:", html)
                self.assertIn("¡Hola mundo!", html)
                self.assertIn('translation/add', html)
                self.assertIn('phrasebook/add', html)
                self.assertEqual(session['lang_from'], "EN")
                self.assertEqual(session['lang_to'], "ES")
                self.assertIsNotNone(session['last_translation'])
                self.assertEqual(session['last_translation']['text_from'], "hello world!")
                self.assertEqual(session['last_translation']['text_to'], "¡Hola mundo!")
                self.assertEqual(session['last_translation']['lang_from'], "EN")
                self.assertEqual(session['last_translation']['lang_to'], "ES")
                self.assertIsNone(session['last_translation']['id'])
                

    def test_clear_translation(self):
        """Does route clear homepage translation result?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess["last_translation"] = {"id": None,
                                            "lang_from": "EN",
                                            "lang_to": "ES",
                                            "text_from": "Hello world!",
                                            "text_to": "¡Hola mundo!"}
            resp = c.get("/")
            self.assertIn("Hola mundo!", str(resp.data))
            
            resp = c.get("/clear", follow_redirects=True) 
            self.assertNotIn("Hola mundo!", str(resp.data))
            self.assertIsNone(session.get("last_translation"))
