"""Phrasebook model tests"""

# run these tests like:
#
#    python -m unittest test_user_model.py

import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Phrasebook, Translation, PhrasebookTranslation

os.environ["DATABASE_URL"] = "postgresql:///translator-test"


from app import app


# app.config['TESTING'] = True
# app.config['DEBUG_TB_HOSTS'] = ['dont-show-debug-toolbar']


with app.app_context():
    db.create_all()


class PhrasebookModelTestCase(TestCase):
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

        self.client = app.test_client()

    def tearDown(self):
        """Clean up any fouled transaction."""
        db.session.rollback()

    def test_phrasebook_model(self):
        """Does basic phrasebook model relationships work?"""

        # phrasebook.user
        self.assertEqual(self.p1.user, self.u1)
        self.assertNotEqual(self.p2.user, self.u1)

        # phrasebook.translations
        self.assertIn(self.t1, self.p1.translations)
        self.assertNotIn(self.t1, self.p2.translations)
        self.assertEqual(len(self.p1.translations), 2)

        # phrasebook_translation association
        p1_t1 = PhrasebookTranslation.query.get((self.pid1, self.tid1))
        self.assertIsNotNone(p1_t1)
        self.assertIsNone(p1_t1.note)

        self.assertIsNotNone(self.p2_t2.note)

        p2_t1 = PhrasebookTranslation.query.get((self.pid2, self.tid1))
        self.assertIsNone(p2_t1)

    ####
    #
    # Delete Cascade tests
    #
    ####
    def test_delete_phrasebook_cascade(self):
        """phrasebook.delete() should delete the phrasebook, all orphaned translations, and all phrasebook_translation associations"""

        self.p1.delete()
        p1 = Phrasebook.query.get(self.pid1)
        t1 = Translation.query.get(self.tid1)
        t2 = Translation.query.get(self.tid2)
        p1_t1 = PhrasebookTranslation.query.get((self.pid1, self.tid1))
        p1_t2 = PhrasebookTranslation.query.get((self.pid1, self.tid2))

        self.assertIsNone(p1)

        # t1 is an orphaned translation
        self.assertIsNone(t1)
        self.assertIsNone(p1_t1)

        # t2 still associated with another user's phrasebook
        self.assertIsNotNone(t2)
        self.assertIsNone(p1_t2)

    def test_delete_phrasebook_translation(self):
        """phrasebook.delete_translation(translation) should delete the phrasebook_translation association. If the trnaslation is orphaned and is no longer associated with any phrasebooks, it too should be deleted."""

        self.assertEqual(len(self.p1.translations), 2)
        self.assertIn(self.t1, self.p1.translations)
        self.assertIn(self.t2, self.p1.translations)

        # delete translation 2
        self.p1.delete_translation(self.t2)
        db.session.commit()

        p1 = Phrasebook.query.get(self.pid1)
        t2 = Translation.query.get(self.tid2)
        p1_t2 = PhrasebookTranslation.query.get((self.pid1, self.tid2))

        # translation2's phrasbook_translation association should be deleted, but the translations should exist since it still has an association with another phrasebook.
        self.assertEqual(len(p1.translations), 1)
        self.assertNotIn(t2, p1.translations)
        self.assertIsNone(p1_t2)
        self.assertIsNotNone(t2)

        # delete translation 1
        self.p1.delete_translation(self.t1)
        db.session.commit()

        p1 = Phrasebook.query.get(self.pid1)
        t1 = Translation.query.get(self.tid1)
        p1_t1 = PhrasebookTranslation.query.get((self.pid1, self.tid1))

        # translation1 only belongs to the one deleted phrasebook, so it and all of it's associations should be deleted.
        self.assertEqual(len(p1.translations), 0)
        self.assertNotIn(t1, p1.translations)
        self.assertIsNone(p1_t1)
        self.assertIsNone(t1)
