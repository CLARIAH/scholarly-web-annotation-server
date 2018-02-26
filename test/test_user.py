import unittest
from models.user import User, pwd_context
from models.error import UserError

class TestUser(unittest.TestCase):

    def setUp(self):
        self.username = "testuser"
        self.password = "testpass"
        self.wrong_pass = "testpass1"
        self.secret_key = "to test or not to test"

    def test_user_model_rejects_init_without_argument(self):
        error = None
        try:
            User()
        except TypeError as e:
            error = e
        self.assertNotEqual(error, None) # error must be defined

    def test_user_model_rejects_init_without_username(self):
        error = None
        try:
            User({})
        except UserError as e:
            error = e
        self.assertNotEqual(error, None) # error must be defined
        self.assertEqual(error.message, "user_data must have property 'username'")

    def test_user_model_rejects_init_with_non_object(self):
        error = None
        try:
            User(9)
        except TypeError as e:
            error = e
        self.assertNotEqual(error, None) # error must be defined

    def test_user_model_rejects_init_with_nonstring_username(self):
        error = None
        try:
            User({"username": 9})
        except UserError as e:
            error = e
        self.assertNotEqual(error, None) # error must be defined
        self.assertEqual(error.message, "username must be a string")

    def test_user_model_accepts_init_with_username(self):
        user = User({"username": self.username})
        self.assertEqual(user.username, self.username)

    def test_user_model_rejects_nonstring_password(self):
        user = User({"username": self.username})
        error = None
        try:
            user.hash_password(9)
        except TypeError as e:
            error = e
        self.assertNotEqual(error, None) # error must be defined

    def test_user_model_accepts_string_password(self):
        user = User({"username": self.username})
        user.hash_password(self.password)
        self.assertTrue(pwd_context.verify(self.password, user.password_hash))

    def test_user_model_rejects_wrong_password(self):
        user = User({"username": self.username})
        user.hash_password(self.password)
        self.assertFalse(user.verify_password(self.wrong_pass))

    def test_user_object_has_json_representation(self):
        user = User({"username": self.username})
        user.hash_password(self.password)
        user_json = user.json()
        self.assertEqual(user_json["username"], self.username)
        self.assertTrue("password_hash" in user_json)


