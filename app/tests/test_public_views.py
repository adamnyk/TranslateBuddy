"""Public views tests"""

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


class PublicViewsTestCase(TestCase):
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


    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

##################################################
# Public routes tests
##################################################
    def test_show_public_phraebooks(self):
        """If logged in, does route show public phrasebooks that do not belong to the current user?"""
        p3 = Phrasebook(name="secondbook", user_id=self.uid1, lang_from="EN", lang_to="ES", public=True)
        p3.id = 333
        db.session.add(p3)
        p3.translations.append(self.t3)
        db.session.commit()
        
        self.assertIn(self.t3, p3.translations)
        
        with self.client as c:
            """Access should be blocked and user redirected home if not logged in."""
            resp = c.get("/public", follow_redirects=True)
            html = resp.get_data(as_text=True)
            self.assertEqual(resp.status_code, 200)

            self.assertIn('Access unauthorized', str(resp.data))
            
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid2
            
            # If logged in...
            resp = c.get("/public", follow_redirects=True)
            
            self.assertEqual(resp.status_code, 200)
            soup = BeautifulSoup(str(resp.data), 'html.parser')

            # Only non-user public phrasebooks should be shown
            phrasebooks = soup.find_all("a", {"class": "pb-button"})
            self.assertEqual(len(phrasebooks), 2)
            self.assertIn("phrasebook", phrasebooks[0].text)
            self.assertIn("secondbook", phrasebooks[1].text)
            self.assertNotIn("french phrases", phrasebooks[0].text)
            self.assertNotIn("french phrases", phrasebooks[1].text)
        
            # Phrasebooks should contain the text of their translations and no others
            translations_from = [t.get_text() for t in soup('td', {"class": "from"})]
            translations_from[0] = "What's going on, pumpkin?"
            translations_from[1] = 'What a test!'
            translations_from[2] = "I'm orphaned data"
            self.assertEqual(len(translations_from), 3)
            

    def test_add_public_translation(self):
        """Does route add public translation to users's selected phrasebooks.
        If no data is submitted, appropriate alret should be shown and redirected to public page."""
        
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
            
            # Failing case / no data
            resp = c.post(f"/public/translation/{self.tid3}/add",
                        data={"phrasebooks": []},  
                            follow_redirects=True)
            html = resp.get_data(as_text=True)
            
            self.assertIn('No data submitted', html)
            self.assertEqual(resp.status_code, 200 or 202)


    def test_copy_public_phrasebook(self):        
        """Does route copy public phrasebook and all of it's translations to the user's phrasebook."""
        
        self.assertNotIn(self.t2, self.u1.phrasebooks)

        with self.client as c:
            # Access should be blocked and user redirected home if not logged in.
            
            resp = c.post("/public/phrasebook/1/add", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn('Access unauthorized', str(resp.data))
            
            # Show that phrasebook2 is not in user1's phrasebooks
            self.assertNotIn(self.p2, self.u1.phrasebooks)
            self.assertEqual(len(self.u1.phrasebooks), 1)
            
            # Route should sucessfully add public phrasebook2 and it's translations to user1.
            with c.session_transaction() as session:
                session[CURR_USER_KEY] = self.uid1
            
            u1 = User.query.get(self.uid1)
            u1_pbs = u1.phrasebooks
            p2 = Phrasebook.query.get(self.pid2)
            self.assertEqual(len(p2.translations), 1)
            
            resp = c.post(f"/public/phrasebook/{self.pid2}/add", follow_redirects=True)
            u1 = User.query.get(self.uid1)
            
            # there should be one more phrasebook for user1
            self.assertEqual(len(u1.phrasebooks), 2)
            
            # the new phrasebook should contian all of the same data and translationsas the coppied one, except phrasebook id and user_id
            new_p = u1.phrasebooks[1]
            self.assertEqual(new_p.name, p2.name)
            self.assertEqual(new_p.lang_from, p2.lang_from)
            self.assertEqual(new_p.lang_to, p2.lang_to)
            self.assertNotEqual(new_p.user_id, p2.user_id)
            self.assertNotEqual(new_p.id, p2.id)
            self.assertEqual(new_p.user_id, self.uid1)
            
            # new phrasebook should contain the same translations as the copied phrasebook
            p2 = Phrasebook.query.get(self.pid2)
            self.assertEqual(new_p.translations, p2.translations)

            

            