"""User model tests"""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os 
from unittest import TestCase
from sqlalchemy import exc 

from models import db, User, Phrasebook, Translation, PhrasebookTranslation

os.environ['DATABASE_URL'] = "postgresql:///translator-test"


from app import app 


# app.config['TESTING'] = True
# app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


with app.app_context():
    db.create_all()
    
    
class UserModelTestCase(TestCase):
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
            lang_from='EN', 
            lang_to='ES')
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
            lang_from='EN', 
            lang_to='FR')
        pid2 = 2
        p2.id = pid2
        db.session.add(p2)
        db.session.commit()
       
        p2 = Phrasebook.query.get(pid2)
        self.p2 = p2
        self.pid2 = pid2

        
        # Create translation and add to user 1's only phrasebook.
        t1 = Translation(
            lang_from='EN',
            lang_to='ES',
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
            lang_from='EN',
            lang_to='FR',
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
        
        self.client = app.test_client()
        
    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()
    
    def test_user_model(self):
        """Does basic model work?"""

        u = User(
            username="test",
            password="HASHED_PASSWORD"
        )

        db.session.add(u)
        db.session.commit()

        # User should have no phraseboosk
        self.assertEqual(len(u.phrasebooks), 0)
        
    ####
    #
    # Register User Tests
    #
    ####
    def test_valid_signup(self):
        u_test = User.signup("testtesttest", "password")
        uid = 99999
        u_test.id = uid
        db.session.commit()

        u_test = User.query.get(uid)
        self.assertIsNotNone(u_test)
        self.assertEqual(u_test.username, "testtesttest")
        self.assertNotEqual(u_test.password, "password")
        # Bcrypt strings should start with $2b$
        self.assertTrue(u_test.password.startswith("$2b$"))

    def test_invalid_username_signup(self):
        invalid = User.signup(None, "password")
        uid = 123456789
        invalid.id = uid
        with self.assertRaises(exc.IntegrityError) as context:
            db.session.commit()

    def test_invalid_password_signup(self):
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", None)
        
        with self.assertRaises(ValueError) as context:
            User.signup("testtest", "")
            
    ####
    #
    # Authentication Tests
    #
    ####
    def test_valid_authentication(self):
        u = User.authenticate(self.u1.username, "password")
        self.assertIsNotNone(u)
        self.assertEqual(u.id, self.uid1)
    
    def test_invalid_username(self):
        self.assertFalse(User.authenticate("badusername", "password"))

    def test_wrong_password(self):
        self.assertFalse(User.authenticate(self.u1.username, "badpassword"))
        
    ####
    #
    # Cascade on delete test
    #
    ####
    def test_user_delete_cascade(self):
        """Test if user.delete() method deletes user and that user's phrasebooks.
        All translations should be deleted from the database if their only parent has been deleted."""
        
        self.assertIsNotNone(self.u1)
        self.assertIsNotNone(self.p1)
        self.assertEqual(len(self.u1.phrasebooks), 1)
        self.assertEqual(self.u1.phrasebooks[0], self.p1)
        
        self.u1.delete()
        db.session.commit()
        
        u = User.query.get(self.uid1)
        p = Phrasebook.query.get(self.pid1)
        
        self.assertIsNone(u)
        self.assertIsNone(p)
        
        # translation1's only parent has been deleted, so it too should be deleted
        t1 = Translation.query.get(self.tid1)
        self.assertIsNone(t1)
        
        # Translation2, though associated with the deleted phrasebook, still belongs to a phrasebook belonging to User2, and should still persist in the database.
        t2 = Translation.query.get(self.tid2)
        self.assertIsNotNone(t2)
        
