import unittest
from models.user import User, UserError
from models.user_store import UserStore
from elasticsearch import Elasticsearch
import time
from itsdangerous import (TimedJSONWebSignatureSerializer
                        as Serializer, BadSignature, SignatureExpired)

class TestUserStore(unittest.TestCase):

    def setUp(self):
        self.config = {
            "host": "localhost",
            "port": 9200,
            "user_index": "unittest-test-index"
        }
        self.remove_test_index() # make sure there is no previous test index
        self.testname = "testname"
        self.testpass = "testpass"
        self.testuser = {"username": self.testname, "password": self.testpass}
        self.user_store = UserStore(configuration=self.config)

    def remove_test_index(self):
        es = Elasticsearch([{"host": self.config['host'], "port": self.config['port']}])
        if es.indices.exists(index=self.config["user_index"]):
            es.indices.delete(index=self.config["user_index"])

    def add_test_user(self):
        user = User({"username": self.testname})
        user.hash_password(self.testpass)
        return self.user_store.add_user_to_index(user)

    def tearDown(self):
        self.remove_test_index() # make sure to remove test index

    def test_user_can_be_initialised(self):
        self.user_store = UserStore(self.config)

    def test_store_cannot_add_user_to_index_without_password(self):
        user = User({"username": self.testname})
        error = None
        try:
            self.user_store.add_user_to_index(user)
        except UserError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Cannot store user without a password")

    def test_store_can_add_user_to_index_with_password(self):
        user = User({"username": self.testname})
        user.hash_password(self.testpass)
        self.user_store.add_user_to_index(user)
        newuser = self.user_store.get_user_from_index(self.testname)
        self.assertEqual(newuser.username, self.testname)
        self.assertEqual(newuser.password_hash, user.password_hash)

    def test_store_cannot_delete_user_from_index_without_password(self):
        self.add_test_user()
        user = User({"username": self.testname})
        error = None
        try:
            self.user_store.delete_user_from_index(user)
        except UserError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Cannot delete user without a password")

    def test_store_can_delete_user_from_index_with_password(self):
        user = User({"username": self.testname})
        user.hash_password(self.testpass)
        self.user_store.add_user_to_index(user)
        self.user_store.delete_user_from_index(user)
        bool_exists = self.user_store.user_exists(self.testname)
        self.assertEqual(bool_exists, False)

    def test_store_can_check_user_does_not_exists(self):
        val = self.user_store.user_exists(self.testname)
        self.assertFalse(val)

    def test_store_can_check_user_does_exists(self):
        user = self.add_test_user()
        self.assertTrue(self.user_store.user_exists(user.user_id))

    def test_store_can_register_new_user(self):
        user = self.user_store.register_user(self.testname, self.testpass)
        self.assertTrue(self.user_store.user_exists(user.user_id))
        retrieved_user = self.user_store.get_user_from_index(username=self.testname)
        self.assertEqual(user.username, retrieved_user.username)

    def test_store_can_get_existing_user(self):
        self.add_test_user()
        user = self.user_store.get_user(self.testname)
        self.assertEqual(self.testname, user.username)

    def test_store_cannot_update_incorrect_password(self):
        self.add_test_user()
        user = self.user_store.get_user_from_index(username=self.testname)
        error = None
        try:
            self.user_store.update_password(user.username, "wrong_password", "new_password")
        except UserError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Incorrect password")

    def test_store_can_update_password(self):
        self.add_test_user()
        user = self.user_store.get_user_from_index(username=self.testname)
        self.user_store.update_password(user.username, self.testpass, "new_password")
        user = self.user_store.get_user_from_index(username=self.testname)
        self.assertTrue(user.verify_password("new_password"))

    def test_store_cannot_delete_user_without_password_hash(self):
        self.add_test_user()
        user = User({"username": self.testname})
        error = None
        try:
            self.user_store.delete_user(user)
        except UserError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Cannot delete user without a password")

    def test_store_can_delete_user(self):
        user = self.add_test_user()
        self.user_store.delete_user(user)
        self.assertEqual(self.user_store.user_exists(self.testname), False)

    def test_user_store_can_generate_auth_token(self):
        user = self.add_test_user()
        token = self.user_store.generate_auth_token(user.user_id, expiration=600)
        s = Serializer(self.user_store.secret_key)
        data = s.loads(token)
        self.assertEqual(user.user_id, data["user_id"])

    def test_user_auth_token_can_expire(self):
        user = self.add_test_user()
        token = self.user_store.generate_auth_token(user.user_id, expiration=0.1)
        time.sleep(1)
        s = Serializer(self.user_store.secret_key)
        error = None
        try:
            s.loads(token)
        except SignatureExpired as err:
            error = err
        self.assertNotEqual(error, None)

    def test_user_object_can_verify_auth_token(self):
        user = self.add_test_user()
        token = self.user_store.generate_auth_token(user.user_id, expiration=0.1)
        verified_user = self.user_store.verify_auth_token(token)
        self.assertEqual(verified_user.user_id, user.user_id)



