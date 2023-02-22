"""Phrasebook views tests"""

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


class PhrasebookViewsTestCase(TestCase):
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
        pid1 = 111
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
            public=True,
            lang_from="EN",
            lang_to="FR",
        )
        pid2 = 222
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
        tid1 = 111
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
        tid2 = 222
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
        tid3 = 333
        t3.id = tid3
        db.session.add(t3)
        db.session.commit()

        t3 = Translation.query.get(tid3)
        self.t3 = t3
        self.tid3 = tid3

        db.session.commit()

        p3 = Phrasebook(name="secondbook", user_id=self.uid1, lang_from="EN", lang_to="ES", public=True)
        p3id = 333
        p3.id = p3id
        db.session.add(p3)
        p3.translations.append(self.t3)
        db.session.commit()
        
        p3 = Phrasebook.query.get(p3id)
        self.p3 = p3
        self.pid3 = p3id

        db.session.commit()


    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
    
    
##################################################
# User phrasebooks tests
##################################################
    def test_view_all_phrasebooks(self):
        """If logged in, does route show user phrasebooks and their translations? If not logged in, does route display unauthorized message and redirect home"""

        with self.client as c:
            """Access should be blocked and user redirected home if not logged in."""
            resp = c.get("/user", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            
            # If logged in...
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
                
            resp = c.get("/user", follow_redirects=True)
            soup = BeautifulSoup(str(resp.data), 'html.parser')

            # Only logged in user's phrasebooks should be shown
            phrasebooks = soup.find_all("a", {"class": "pb-button"})
            self.assertEqual(len(phrasebooks), 2)
            self.assertIn("phrasebook", phrasebooks[0].text)
            self.assertIn("secondbook", phrasebooks[1].text)
            self.assertNotIn("french phrases", phrasebooks[0].text)
            self.assertNotIn("french phrases", phrasebooks[1].text)
            
            # Both phrasebooks are public and should show globe icons
            public_icons = soup.find_all("i", {"class": "public-globe"})
            self.assertEqual(len(public_icons), 2)
        
            # Phrasebooks should contain the text of their translations and no others
            translations_from = [t.get_text() for t in soup('td', {"class": "from"})]
            translations_from[0] = "What's going on, pumpkin?"
            translations_from[1] = 'What a test!'
            translations_from[2] = "I'm orphaned data"
            self.assertEqual(len(translations_from), 3)    
        
    def test_add_phrasebook(self):
        """If logged in, does route add new phrasebook and assign it to the current user. If not logged in, does route display unauthorized message and redirect home"""
        
        with self.client as c:
            """Access should be blocked and user redirected home if not logged in."""
            resp = c.post("/phrasebook/add", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            
            # If logged in...
            u1 = User.query.get(self.uid1)
            self.assertEqual(len(u1.phrasebooks), 2)

            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
            
            resp = c.post("/phrasebook/add",
                          data={"name": "Conversation",
                                "lang_from": "EN",
                                "lang_to": "FR",},
                          follow_redirects=True)
            
            u1 = User.query.get(self.uid1)
            self.assertEqual(len(u1.phrasebooks), 3)
            
            new_pb= u1.phrasebooks[2]
            self.assertEqual(new_pb.name, "Conversation")
            self.assertEqual(new_pb.user_id, self.uid1)
            self.assertEqual(new_pb.lang_from, "EN")
            self.assertEqual(new_pb.lang_to, "FR")
            self.assertEqual(new_pb.public, False)

    
    def test_edit_phrasebook(self):
        """Route should edit existing user phraebook name / public status.
        If not logged in, or accessing another user's phrasebook, redirect user and send unauthorized message."""
        with self.client as c:
            resp = c.post(f"/phrasebook/{self.pid2}/edit",
                          follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            
        with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1  
        
        # if phrasebook does not belong to user, redirect and send message
        resp = c.post(f"/phrasebook/{self.pid2}/edit", 
                       data={"name": "edited name", "public": False},
                       follow_redirects=True)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('Access unauthorized', str(resp.data))
        
        resp = c.post(f"/phrasebook/{self.pid1}/edit", 
                       data={"name": "edited name", "public": 'false'},
                       follow_redirects=True)
        
        pb1_edited = Phrasebook.query.get(self.pid1)
        
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(pb1_edited.name, "edited name")
        self.assertEqual(pb1_edited.public, False)
        self.assertEqual(pb1_edited.user_id, self.pid1)
        self.assertIn("Phrasebook updated.", str(resp.data))


    def test_delete_phrasebook(self):
        """Does route delete phrasebook"""
        
        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1  
            
            pb = Phrasebook.query.get(self.pid1)

            resp = c.post(f"/phrasebook/{self.pid1}/delete", 
                       follow_redirects=True)
                    
            self.assertIn(f"Phrasebook deleted", str(resp.data))
            pb = Phrasebook.query.get(self.pid1)
            self.assertIsNone(pb)


    def test_add_translation(self):
        """Should create a new translation from session contents and add to current user's phrasebooks.If no data is submitted, redirect and flash message."""
        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
                session['last_translation'] = {'id': 666, 
                                               'lang_from': 'EN', 
                                               'lang_to': 'NB', 
                                               'text_from': 'Test translation', 
                                               'text_to': 'Test oversettelse'} 
            
            # If submitted with no data, should redirect and flash message
            resp = c.post(f"/translation/add", follow_redirects=True)
            self.assertIn("No data submitted", str(resp.data))
            
            # Success case. Translation should be in both phrasebooks
            resp = c.post("/translation/add",
                          data={"phrasebooks": [self.pid1, self.pid3]},
                          follow_redirects=True)
            
            self.assertIn("Translation saved.", str(resp.data))
            p1 = Phrasebook.query.get(self.pid1)
            p3 = Phrasebook.query.get(self.pid3)
            t = Translation.query.get(666)
            self.assertIn(t, p1.translations)
            self.assertIn(t, p3.translations)
            
    
    def test_delete_translation(self):
        """Does route delete translation from phrasebook? If translation is not used by any other phrasebook, the translation itself should be deleted from the database"""
        
        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
                   
            resp = c.post(f"/phrasebook/{self.pid1}/translation/{self.tid1}/delete",
                          follow_redirects=True)
            
            t1 = Translation.query.get(self.tid1)
            p1 = Phrasebook.query.get(self.pid1)
            
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Translation deleted.", str(resp.data))
            self.assertNotIn(t1, p1.translations)
            
            # translation t1 should be deleted from database since it is only in phrasebook 1
            self.assertIsNone(t1)
            
            resp = c.post(f"/phrasebook/{self.pid1}/translation/{self.tid2}/delete",
                          follow_redirects=True)
            
            t2 = Translation.query.get(self.tid2)
            p1 = Phrasebook.query.get(self.pid1)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Translation deleted.", str(resp.data))
            self.assertNotIn(t2, p1.translations)
            
            # translation t2 should still exist since it is also referenced by phraebook 2
            self.assertIsNotNone(t2)



    def test_edit_translation_note(self):
        """Does route add note to phrasebook_translation association?"""
        
        pb_t = PhrasebookTranslation.query.get((self.pid1, self.tid1))
        note = pb_t.note
        self.assertIsNone(note)
        
        with self.client as c:
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
                
            resp = c.post(f"/{self.pid1}/{self.tid1}/note",
                          data = {"note": "testing... testing..."},
                          follow_redirects=True)
            
            pb_t = PhrasebookTranslation.query.get((self.pid1, self.tid1))
            note = pb_t.note
            self.assertEqual(resp.status_code, 200)
            self.assertEqual(note, "testing... testing...")

            # testing note deletion
            resp = c.post(f"/{self.pid1}/{self.tid1}/note",
                          data = {"note": None},
                          follow_redirects=True)
            
            pb_t = PhrasebookTranslation.query.get((self.pid1, self.tid1))
            note = pb_t.note
            self.assertEqual(resp.status_code, 200)
            self.assertIsNone(note)
