from typing import Dict, Union
from models.user import User
from models.error import UserError
from elasticsearch import Elasticsearch
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired


class UserStore(object):

    def __init__(self, es_config: Dict[str, Union[str, int]]):
        self.secret_key = "some combination of key words"
        if "secret_key" in es_config:
            self.secret_key = es_config["secret_key"]

        # initialise ES
        self.es_config = es_config
        self.es_index = es_config['user_index']
        self.es = Elasticsearch([{"host": es_config['host'], "port": es_config['port']}])
        if not self.es.indices.exists(index=self.es_index):
            self.es.indices.create(index=self.es_index)
        self.needs_refresh = False

    def configure(self, es_config: Dict[str, Union[str, int]]) -> None:
        self.es_config = es_config
        self.es_index = es_config['user_index']
        self.es = Elasticsearch([{"host": es_config['host'], "port": es_config['port']}])
        if not self.es.indices.exists(index=self.es_index):
            self.es.indices.create(index=self.es_index)
        self.needs_refresh = False

    def index_needs_refresh(self):
        return self.needs_refresh

    def index_refresh(self):
        self.es.indices.refresh(index=self.es_index)
        self.needs_refresh = False

    def set_index_needs_refresh(self):
        self.needs_refresh = True

    def check_index_is_fresh(self):
        # check index is up to date, refresh if needed
        if self.index_needs_refresh():
            self.index_refresh()

    def register_user(self, username, password):
        if not self.username_available(username):
            raise UserError(f"User {username} already exists!")
        user = User({"username": username})
        user.hash_password(password)
        response = self.add_user_to_index(user)
        return response

    def username_available(self, username):
        response = self.es.search(index=self.es_index, body={"query": {"match": {"username": username}}})
        return True if response["hits"]["total"] == 0 else False

    def get_user_from_index(self, username=None, user_id=None):
        if not username and not user_id:
            return None
        if user_id and not self.user_exists(user_id):
            raise UserError("User {u} doesn't exist".format(u=username))
        if user_id:
            response = self.es.get(index=self.es_index, doc_type="user", id=user_id)
            return User(response["_source"])
        response = self.es.search(index=self.es_index, body={"query": {"match": {"username": username}}})
        if response["hits"]["total"] == 0:
            raise UserError("User {u} doesn't exist".format(u=username))
        return User(response["hits"]["hits"][0]["_source"])

    def verify_user(self, username, password):
        user = self.get_user_from_index(username=username)
        if user and user.verify_password(password):
            return True
        else:
            return False

    def generate_auth_token(self, user_id, expiration=600):
        s = Serializer(self.secret_key, expires_in=expiration)
        return s.dumps({"user_id": user_id})

    def verify_auth_token(self, token):
        s = Serializer(self.secret_key)
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None
        except BadSignature:
            return None
        return self.get_user_from_index(user_id=data["user_id"])

    def get_user(self, username):
        return self.get_user_from_index(username=username)

    def delete_user(self, user):
        return self.delete_user_from_index(user)

    def update_password(self, username, password, new_password):
        if not self.verify_user(username, password):
            raise UserError(message="Incorrect password")
        user = self.get_user(username)
        user.hash_password(new_password)
        return self.add_user_to_index(user)

    def user_exists(self, user_id):
        return self.es.exists(index=self.es_index, doc_type="user", id=user_id)

    def add_user_to_index(self, user):
        if not user.password_hash:
            raise UserError("Cannot store user without a password")
        # action = "updated" if self.user_exists(user.username) else "created"
        self.es.index(index=self.es_index, doc_type="user", id=user.user_id, body=user.json())
        self.es.indices.refresh(index=self.es_index)
        return user

    def delete_user_from_index(self, user):
        if not user.password_hash:
            raise UserError("Cannot delete user without a password")
        self.es.delete(index=self.es_index, doc_type="user", id=user.user_id)
        self.es.indices.refresh(index=self.es_index)
        return user

