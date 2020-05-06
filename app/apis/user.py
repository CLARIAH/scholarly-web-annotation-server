from typing import Dict, Union
import logging
from flask import request, abort, make_response, jsonify, g
from flask_restx import Namespace, Resource, fields
from models.user_store import UserStore
from settings import server_config
from flask_httpauth import HTTPBasicAuth

user_store = UserStore(server_config["Elasticsearch"])
api = Namespace('users', description='User related operations')
fh = logging.FileHandler("v1-users.log")
api.logger.addHandler(fh)
auth = HTTPBasicAuth()


# user model
user_model = api.schema_model("User", {
    "properties": {
        "username": {
            "type": "string"
        },
        "email": {
            "type": "string"
        }
    }
})

# user has been created response model
user_response = api.model("UserResponse", {
    "action": fields.String(descrption="Update action", require=True,
                            enum=["created", "verified", "updated", "deleted"]),
    "user": fields.Nested(user_model, require=False)
})


@auth.verify_password
def verify_password(token_or_username, password):
    # print('verifying password')
    # anonymous access is allowed, set user to None
    api.logger.info('attempt to authenticate')
    if not token_or_username and not password:
        # anonymous user
        g.user = None
        return True
    # Non-anonymous access requires authentication
    # First try to authenticate by token
    g.user = user_store.verify_auth_token(token_or_username)
    if g.user:
        return True
    if user_store.verify_user(token_or_username, password):
        g.user = user_store.get_user(token_or_username)
        return True
    # non-anoymous user not authenticated -> return error 403
    return False

# handled by HTTPBasicAuth
@auth.error_handler
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)


# Update configuration
def configure_store(config: Dict[str, Union[str, int]]):
    user_store.configure(config)


"""--------------- User endpoints ------------------"""


@api.route("/")
class UsersApi(Resource):

    @api.response(201, 'Success', user_response)
    @api.response(400, 'Invalid user data')
    @api.response(403, 'User already exists')
    @api.expect(user_model)
    def post(self):
        user_details = request.get_json()
        if "username" not in user_details or "password" not in user_details:
            return {"message": "user data requires 'username' and 'password'"}, 400
        if user_store.user_exists(user_details['username']):
            abort(403)
        user = user_store.register_user(user_details["username"], user_details["password"])
        token = user_store.generate_auth_token(user.user_id, expiration=600)
        api.logger.info('user with name %s created successfully', user.username)
        return {"action": "created",  "user": {"username": user.username, "token": token.decode('ascii')}}, 201

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(403, 'Unauthorized access')
    @api.response(404, 'User does not exist')
    @api.expect(user_model)
    def put(self):
        user_details = request.get_json()
        if "new_password" not in user_details or "password" not in user_details:
            return {"message": "password update requires 'password' and 'new_password'"}, 400
        user = user_store.update_password(g.user.username, user_details["password"], user_details["new_password"])
        response = {"action": "updated", "user": user.json()}
        del response["user"]["password_hash"]
        api.logger.info('user with name %s updated successfully', user.username)
        return response, 200

    @auth.login_required
    @api.response(204, 'Success', user_response)
    def delete(self):
        user_store.delete_user(g.user)
        api.logger.info('user with name %s updated successfully', g.user.username)
        return {'message': 'user deleted'}, 204


@api.route("/login")
class LoginApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(403, 'Unauthorized access')
    @api.response(404, 'User does not exist')
    def post(self):
        if not g.user:
            # if no user object is POSTed, this is a bad request
            abort(403)
        token = user_store.generate_auth_token(g.user.user_id, expiration=600)
        api.logger.info('user with name %s logged in successfully', g.user.username)
        return {"action": "authenticated", "user": {"username": g.user.username, "token": token.decode('ascii')}}, 200


@api.route("/logout")
class LogoutApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def get(self):
        # once token-based auth is implemented, remove token upon logout
        api.logger.info('user with name %s logged out successfully', 'bla')
        return {"action": "logged out"}, 200
