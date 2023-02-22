"""Home views tests"""

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
# Homepage tests
##################################################

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
            

