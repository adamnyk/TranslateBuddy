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


from app import app, CURR_USER_KEY

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

#########################
# Homepage tests
    def test_home_logged_out(self):
         with self.client as c:
             resp = c.get("/")
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)
             
             self.assertIn('Login or register to view and create phrasebooks!', html)
             self.assertNotIn('href="/user', html)
             self.assertNotIn('href="/logout', html)
             self.assertNotIn('href="/public', html)
             self.assertIn('>Login</a>', html)
             self.assertIn('>Register</a>', html)
             self.assertIn('Translate\n\t\t\t\t\t</button>', html)
             
    def test_home_logged_in(self):
         with self.client as c:
             with c.session_transaction() as sess:
                 sess[CURR_USER_KEY] = self.uid1
                 
             resp = c.get("/")
             html = resp.get_data(as_text=True)
             self.assertEqual(resp.status_code, 200)
             
             self.assertNotIn('Login or register to view and create phrasebooks!', html)
             self.assertIn('/user', html)
             self.assertIn('/logout', html)
             self.assertIn('/public', html)
             self.assertNotIn('>Login</a>', html)
             self.assertNotIn('>Register</a>', html)
             self.assertIn('Translate\n\t\t\t\t\t</button>', html)
            

#########################
# Translate tests

        
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
                
    
    
    
    def test_add_public_translation(self):
        """Does route add public translation to users's selected phrasebooks"""
        
        p3 = Phrasebook(name="secondbook", user_id=self.uid1, lang_from="EN", lang_to="ES")
        p3.id = 333
        db.session.add(p3)
        db.session.commit()
       
        with self.client as c:
            
            self.assertEqual(len(self.u1.phrasebooks), 2)
            self.assertEqual(len(p3.translations), 0)

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1


            resp = c.post(f"/public/translation/{self.tid3}/add",
                        data={"phrasebooks": [self.pid1, p3.id]},  
                            follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            p1 = Phrasebook.query.get(self.pid1)
            t3 = Translation.query.get(self.tid3)
            p3 = Phrasebook.query.get(p3.id)
            
            self.assertIn('Translation saved', html)
            self.assertEqual(resp.status_code, 200 or 202)
            self.assertEqual(len(p1.translations), 3)
            self.assertIn(t3, p1.translations)
            self.assertEqual(len(p3.translations), 1)
            self.assertIn(t3, p3.translations)
            
          

