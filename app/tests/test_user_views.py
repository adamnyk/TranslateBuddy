"""User views tests"""

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

app.config["WTF_CSRF_ENABLED"] = False
app.config["TESTING"] = True
app.config["DEBUG_TB_HOSTS"] = ["dont-show-debug-toolbar"]


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

        # create user 2
        u2 = User.signup("testuser2", "password")
        uid2 = 222
        u2.id = uid2
        db.session.commit()

        u2 = User.query.get(uid2)
        self.u2 = u2
        self.uid2 = uid2

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    ##################################################
    # User routes tests
    ##################################################

    def test_signup(self):
        """Does route register new user in database and add user id to session?
        If passwords don't match, reidrect and flash user message.
        If username already exists, redirect and flash user message."""
        with self.client as c:
            # Passwords don't match
            resp = c.post(
                "/signup",
                data={
                    "username": "new_user",
                    "password": "new_pass",
                    "password_confirm": "notmatchingpass",
                },
                follow_redirects=True,
            )

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Registration failed: Passwords must match.", str(resp.data))
            u = User.query.filter_by(username="new_user").first()
            self.assertIsNone(u)

            # Username already exists
            resp = c.post(
                "/signup",
                data={
                    "username": "testuser",
                    "password": "new_pass",
                    "password_confirm": "new_pass",
                },
                follow_redirects=True,
            )

            self.assertEqual(resp.status_code, 200)
            self.assertIn("Username already taken", str(resp.data))

            # Success case
            resp = c.post(
                "/signup",
                data={
                    "username": "new_user",
                    "password": "new_pass",
                    "password_confirm": "new_pass",
                },
                follow_redirects=True,
            )

            self.assertIn("Welcome! Account created.", str(resp.data))
            u = User.query.filter_by(username="new_user").first()
            self.assertIsNotNone(u)
            self.assertEqual(u.username, "new_user")
            self.assertTrue(u.password.startswith("$2b$"))
            self.assertEqual(session[CURR_USER_KEY], u.id)
            self.assertEqual(session["sort"], "id")
            self.assertEqual(session["sort_public"], "id")

    def test_login(self):
        """Does route log in user with correct credentials?"""
        with self.client as c:

            # login with invalid credentials
            resp = c.post(
                "/login",
                data={"username": "fakeuser", "password": "fakepass"},
                follow_redirects=True,
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Invalid login credentials.", str(resp.data))
            u = User.query.filter_by(username="fakeuser").first()
            self.assertIsNone(u)

            # success case
            resp = c.post(
                "/login",
                data={"username": f"testuser", "password": "password"},
                follow_redirects=True,
            )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Hello, testuser!", str(resp.data))
            u = User.query.filter_by(username="testuser").first()
            self.assertIsNotNone(u)
            self.assertEqual(session[CURR_USER_KEY], u.id)

    def test_logout(self):
        """Does route log out user by removing them from session."""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 111

            c.get("/")
            self.assertEqual(session.get(CURR_USER_KEY), 111)
            resp = c.get("/logout", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Goodbye!", str(resp.data))
            self.assertIsNone(session.get(CURR_USER_KEY))

    def test_edit_user(self):
        """Does route edit current user's username if correct password is given?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 111

        # incorrect password
        resp = c.post(
            "/user/edit",
            data={"username": "new_username", "password": "wrong_password"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Wrong password", str(resp.data))
        u = User.query.get(111)
        self.assertNotEqual(u.username, "new_username")

        # username taken
        resp = c.post(
            "/user/edit",
            data={"username": "testuser2", "password": "password"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn("Username already taken", str(resp.data))
        u = User.query.get(111)
        self.assertNotEqual(u.username, "testuser2")

        # success case
        resp = c.post(
            "/user/edit",
            data={"username": "new_user", "password": "password"},
            follow_redirects=True,
        )
        self.assertEqual(resp.status_code, 200)
        u = User.query.get(111)
        self.assertEqual(u.username, "new_user")

    def test_delete_user(self):
        """Does route delete current user and log them out?"""

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = 111

            resp = c.post("/user/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("sucessfully deleted", str(resp.data))
            u = User.query.get(111)
            self.assertIsNone(u)
            self.assertIsNone(session.get(CURR_USER_KEY))
