from flask import Flask, Blueprint, request, abort, make_response, jsonify, g, json
from flask_restx import Api, Resource
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS

from models.response_models import *
from models.error import InvalidUsage
from parse.headers_params import *
from models.annotation_store import AnnotationStore
from models.user_store import UserStore
from models.annotation import AnnotationError
from models.annotation_container import AnnotationContainer

from elasticsearch.exceptions import ConnectionError

from settings import server_config

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/ns/swao', 'swao', lambda: app.send_static_file('vocabularies/index.html'))
app.config['SECRET_KEY'] = "some combination of key words"
cors = CORS(app)
#api = Api(app)
blueprint = Blueprint('api', __name__)
api = Api(blueprint)

auth = HTTPBasicAuth()

try:
    annotation_store = AnnotationStore(server_config["Elasticsearch"])
    user_store = UserStore(server_config["Elasticsearch"])
except ConnectionError:
    print('server_config:', server_config["Elasticsearch"])
    raise

@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.to_dict(), error.status_code

@api.errorhandler(AnnotationError)
def handle_annotation_error(error):
    return error.to_dict(), error.status_code

@auth.verify_password
def verify_password(token_or_username, password):
    print('verifying password')
    # anonymous access is allowed, set user to None
    if not token_or_username and not password:
        g.user = None # anonymous user
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

@auth.error_handler # handled by HTTPBasicAuth
def unauthorized():
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return make_response(jsonify({'message': 'Unauthorized access'}), 403)

@api.errorhandler # handled by Flask restplus api
def handle_unauthorized_api(error):
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return {'message': 'Unauthorized access'}, 403


"""--------------- Ontology endpoints ------------------"""


@app.route("/ns/swao.jsonld", endpoint="swao-jsonld")
def swao():
    with open('./public/vocabularies/swao.json', 'rt') as fh:
        swao = json.load(fh)
        print(swao)
        return swao

"""--------------- Annotation endpoints ------------------"""


@api.route("/api", endpoint='api_base')
class BasicAPI(Resource):

    @api.response(200, 'Success', annotation_list_response)
    @api.response(404, 'Annotation Error')
    def get(self):
        return {"message": "Annotation server online"}

"""--------------- Annotation endpoints ------------------"""


@api.route("/api/annotations", endpoint='annotation_list')
class AnnotationsAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_list_response)
    @api.response(404, 'Annotation Error')
    def get(self):
        params = get_params(request)
        data = annotation_store.get_annotations_es(params)
        container = AnnotationContainer(request.url, data["annotations"], view=params["view"], total=data["total"])
        return container.view()

    @auth.login_required
    @api.response(201, 'Success')
    @api.response(404, 'Invalid Annotation Error')
    @api.expect(annotation_model)
    def post(self):
        params = get_params(request, anon_allowed=False)
        new_annotation = request.get_json()
        response = annotation_store.add_annotation_es(new_annotation, params=params)
        return response, 201

@api.doc(params={'annotation_id': 'The annotation ID'}, required=False)
@api.route('/api/annotations/<annotation_id>', endpoint='annotation')
class AnnotationAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_response)
    @api.response(404, 'Annotation does not exist')
    def get(self, annotation_id):
        params = get_params(request)
        try:
            annotation = annotation_store.get_annotation_es(annotation_id, params)
        except PermissionError:
            abort(403)
        response_data = annotation
        return response_data

    @auth.login_required
    def put(self, annotation_id):
        params = get_params(request, anon_allowed=False)
        annotation = request.get_json()
        response_data = annotation_store.update_annotation_es(annotation, params=params)
        return response_data

    @auth.login_required
    def delete(self, annotation_id):
        params = get_params(request, anon_allowed=False)
        response_data = annotation_store.remove_annotation_es(annotation_id, params)
        return response_data


"""--------------- Collection endpoints ------------------"""


@api.route("/api/collections")
class CollectionsAPI(Resource):

    @auth.login_required
    def post(self):
        #prefer = interpret_header(request.headers)
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection = annotation_store.create_collection_es(collection_data, params)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view(), 201

    @auth.login_required
    def get(self):
        params = get_params(request)
        response_data = []
        collection_data = annotation_store.get_collections_es(params)
        for collection in collection_data["collections"]:
            collection_url = request.url + "/" + collection["id"] + "/annotations/"
            container = AnnotationContainer(collection_url, collection, view=params["view"])
            response_data.append(container.view())
        return response_data

@api.route("/api/collections/<collection_id>")
class CollectionAPI(Resource):

    @auth.login_required
    def get(self, collection_id):
        params = get_params(request)
        collection = annotation_store.get_collection_es(collection_id, params)
        if params["view"] == "PreferContainedDescriptions":
            collection["items"] = annotation_store.get_annotations_by_id_es(collection["items"], params)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    def put(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection = annotation_store.update_collection_es(collection_data)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    def delete(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection = annotation_store.remove_collection_es(collection_id, params)
        return collection

@api.route("/api/collections/<collection_id>/annotations/")
class CollectionAnnotationsAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success')
    @api.response(404, 'Invalid Annotation Error')
    @api.expect(annotation_model)
    def post(self, collection_id):
        params = get_params(request, anon_allowed=False)
        annotation_data = request.get_json()
        if 'id' not in annotation_data.keys():
            annotation_data = annotation_store.add_annotation_es(annotation_data, params)
        collection = annotation_store.add_annotation_to_collection_es(annotation_data['id'], collection_id, params)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    def get(self, collection_id):
        params = get_params(request)
        collection = annotation_store.get_collection_es(collection_id, params)
        if params["view"] == "PreferContainedDescriptions" or ("iris" in params and params["iris"] == 0):
            annotations = annotation_store.get_annotations_by_id_es(collection["items"], params)
            collection["items"] = annotations
        container = AnnotationContainer(request.url, collection["items"], view=params["view"])
        return container.view()

@api.route("/api/collections/<collection_id>/annotations/<annotation_id>")
class CollectionAnnotationAPI(Resource):

    @auth.login_required
    def delete(self, collection_id, annotation_id):
        params = get_params(request, anon_allowed=False)
        return annotation_store.remove_annotation_from_collection_es(annotation_id, collection_id, params)

@api.route("/api/users")
class UsersApi(Resource):

    @api.response(201, 'Success', user_response)
    @api.response(400, 'Invalid user data')
    def post(self):
        user_details = request.get_json()
        if "username" not in user_details or "password" not in user_details:
            return {"message": "user data requires 'username' and 'password'"}, 400
        user = user_store.register_user(user_details["username"], user_details["password"])
        token = user_store.generate_auth_token(user.user_id, expiration=600)
        return {"action": "created",  "user": {"username": user.username, "token": token.decode('ascii')}}, 201

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def put(self):
        user_details = request.get_json()
        if "new_password" not in user_details or "password" not in user_details:
            return {"message": "password update requires 'password' and 'new_password'"}, 400
        user = user_store.update_password(g.user.username, user_details["password"], user_details["new_password"])
        response = {"action": "updated", "user": user.json()}
        del response["user"]["password_hash"]
        return response, 200

    @auth.login_required
    def delete(self):
        user_store.delete_user(g.user)
        return {}, 204

@api.route("/api/login")
class LoginApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def post(self):
        if not g.user:
            abort(403)
        token = user_store.generate_auth_token(g.user.user_id, expiration=600)
        return {"action": "authenticated", "user": {"username": g.user.username, "token": token.decode('ascii')}}, 200

@api.route("/api/logout")
class LogoutApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def get(self):
        # once token-based auth is implemented, remove token upon logout
        return {"action": "logged out"}, 200

app.register_blueprint(blueprint)

if __name__ == "__main__":
    swas_host = server_config["SWAServer"]["host"]
    swas_port = server_config["SWAServer"]["port"]
    app.run(host=swas_host, port=swas_port, debug=True, threaded=True)
