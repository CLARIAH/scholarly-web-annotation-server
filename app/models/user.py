import uuid
from models.error import UserError

#
# import the CryptContext class, used to handle all hashing...
#
from passlib.context import CryptContext

#
# create a single global instance for your app...
#
pwd_context = CryptContext(
    # replace this list with the hash(es) you wish to support.
    # this example sets pbkdf2_sha256 as the default,
    # with support for legacy des_crypt hashes.
    schemes=["pbkdf2_sha256", "des_crypt" ],
    #default="pbkdf2_sha256",

    deprecated="auto",

    # set the number of rounds that should be used...
    pbkdf2_sha256__default_rounds = 80000,
    )

class User(object):

    def __init__(self, user_data):
        if "username" not in user_data:
            raise UserError(message="user_data must have property 'username'")
        if type(user_data["username"]) != str:
            raise UserError(message="username must be a string")
        self.username = user_data["username"]
        self.user_id = user_data["user_id"] if "user_id" in user_data else self.generate_id()
        self.password_hash = user_data["password_hash"] if "password_hash" in user_data else None

    def generate_id(self):
        return uuid.uuid4().urn

    def hash_password(self, password):
        self.password_hash = pwd_context.encrypt(password)

    def verify_password(self, password):
        return pwd_context.verify(password, self.password_hash)

    def json(self):
        return {
            "username": self.username,
            "user_id": self.user_id,
            "password_hash": self.password_hash
        }


