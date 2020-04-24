from flask import Flask, Blueprint, request, abort, make_response, jsonify, g, json
from flask_restx import Api, Resource, Model, fields
from flask_httpauth import HTTPBasicAuth
from flask_cors import CORS

from models.error import InvalidUsage
from parse.headers_params import get_params
from models.annotation_store import AnnotationStore
from models.user_store import UserStore
from models.annotation import AnnotationError
from models.annotation_container import AnnotationContainer
from models.iiif_manifest import Manifest
import models.iiif_manifest as iiif_manifest

from elasticsearch.exceptions import ConnectionError

from settings import server_config

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('index.html'))
app.add_url_rule('/api', 'api_versions', lambda: app.send_static_file('index.html'))
app.add_url_rule('/favicon.ico', 'favicon', lambda: app.send_static_file('favicon.ico'))
app.add_url_rule('/robots.txt', 'robots', lambda: app.send_static_file('robots.txt'))
app.add_url_rule('/ns/swao', 'swao', lambda: app.send_static_file('vocabularies/index.html'))
app.config['SECRET_KEY'] = "some combination of key words"
# app.config['SERVER_NAME'] = 'localhost:3000'
cors = CORS(app)
# api = Api(app)
blueprint = Blueprint('api', __name__, url_prefix='/api/v1')
api = Api(blueprint,
          title='CLARIAH Scholarly Web Annotation Server',
          version='1',
          description='RESTful API for Scholarly Web Annotations',
          # doc='/api'
          )
app.register_blueprint(blueprint)


auth = HTTPBasicAuth()

try:
    annotation_store = AnnotationStore(server_config["Elasticsearch"])
    user_store = UserStore(server_config["Elasticsearch"])
except ConnectionError:
    print('server_config:', server_config["Elasticsearch"])
    raise

"""--------------- API request and response models ------------------"""

# generic response model
response_model = api.model("Response", {
    "status": fields.String(description="Status", required=True, enum=["success", "error"]),
    "message": fields.String(description="Message from server", required=True),
})

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

target_model = api.schema_model("AnnotationTarget", {
    "properties": {
        "id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        },
        "language": {
            "type": "string"
        },
    }
})

body_model = api.schema_model("AnnotationBody", {
    "properties": {
        "id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        },
        "purpose": {
            "type": "string"
        },
        "value": {
            "type": "string"
        },
    },
    "type": "object"
})

new_annotation_model = api.model("NewAnnotation", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    "creator": fields.String(description="Annotation Creator", required=False),
    "body": fields.List(fields.Nested(body_model)),
    "target": fields.List(fields.Nested(target_model))
})

annotation_model = api.model("Annotation", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "id": fields.String(description="Annotation ID", required=False),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    "creator": fields.String(description="Annotation creator", required=False),
    "created": fields.DateTime(description='Annotation created timestamp', required=False),
    "body": fields.List(fields.Nested(body_model)),
    "target": fields.List(fields.Nested(target_model))
})

annotation_page_model = api.model("AnnotationPage", {
    "id": fields.String(description="AnnotationCollection ID", required=False),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["AnnotationPage"]),
    "items": fields.List(fields.Nested(annotation_model)),
})

annotation_collection_model = api.model("AnnotationCollection", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "id": fields.String(description="AnnotationCollection ID", required=False),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["AnnotationCollection"]),
    "creator": fields.String(description="Annotation creator", required=False),
    "label": fields.String(description="Label for the collection of annotions"),
    "created": fields.DateTime(description='Annotation created timestamp', required=False),
    "first": fields.Nested(annotation_page_model),
    "last": fields.String(description="URI for the last AnnotationPage of the collection"),
})

container_model = api.model("AnnotationContainer", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "id": fields.String(description="AnnotationCollection ID", required=False),
    "type": fields.List(fields.String(description="Annotation Type", required=True,
                                      enum=["AnnotationContainer", "BasicContainer"])),
    "total": fields.Integer(description="Total number of annotations in this collection"),
    "first": fields.Nested(annotation_page_model),
    "last": fields.String(description="URI for the last AnnotationPage of the collection"),
})

annotation_response = api.clone("AnnotationResponse", response_model, {"annotation": fields.Nested(annotation_model)})


annotation_list_response = api.model("AnnotationListResponse", {
    "annotations": fields.List(fields.Nested(annotation_model), description="List of annotations")
})

collection_list_model = api.model("AnnotationCollectionListResponse", {
    "collections": fields.List(fields.Nested(annotation_collection_model), description="List of annotation collections")
})


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

# handled by Flask restplus api
@api.errorhandler
def handle_unauthorized_api(_error):
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return {'message': 'Unauthorized access'}, 403


"""--------------- Ontology endpoints ------------------"""


@app.route("/ns/swao.jsonld", endpoint="swao-jsonld")
def swao():
    with open('./public/vocabularies/swao.json', 'rt') as fh:
        swao_json = json.load(fh)
        return swao_json


"""--------------- Annotation endpoints ------------------"""


@api.route("/", endpoint='api_base')
class BasicAPI(Resource):

    @api.response(200, 'Success', response_model)
    @api.response(400, 'API Error', response_model)
    def get(self):
        # print(api.__schema__)
        return {"message": "Annotation server online"}


"""--------------- Annotation endpoints ------------------"""


@api.doc(params={}, required=False)
@api.route("/annotations", endpoint='annotation_list')
class AnnotationsAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(404, 'Annotation Error', response_model)
    def get(self):
        params = get_params(request)
        data = annotation_store.get_annotations_es(params)
        container = AnnotationContainer(request.url, data["annotations"], view=params["view"], total=data["total"])
        return container.view()

    @auth.login_required
    @api.response(201, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(new_annotation_model)
    def post(self):
        params = get_params(request, anon_allowed=False)
        new_annotation = request.get_json()
        response = annotation_store.add_annotation_es(new_annotation, params=params)
        return response, 201


@api.doc(params={'annotation_id': '<annotation_uuid>'}, required=False)
@api.route('/annotations/<annotation_id>', endpoint='annotation')
class AnnotationAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Annotation does not exist', response_model)
    def get(self, annotation_id):
        params = get_params(request)
        try:
            annotation = annotation_store.get_annotation_es(annotation_id, params)
            response_data = annotation
            return response_data
        except PermissionError:
            abort(403)

    @auth.login_required
    @api.response(201, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(annotation_model)
    def put(self, annotation_id):
        params = get_params(request, anon_allowed=False)
        annotation = request.get_json()
        if annotation['id'] != annotation_id:
            raise ValueError('updated annotation has different id from id in request URL')
        response_data = annotation_store.update_annotation_es(annotation, params=params)
        return response_data

    @auth.login_required
    @api.response(204, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, annotation_id):
        params = get_params(request, anon_allowed=False)
        response_data = annotation_store.remove_annotation_es(annotation_id, params)
        return response_data


"""--------------- Collection endpoints ------------------"""


@api.route("/collections")
class CollectionsAPI(Resource):

    @auth.login_required
    @api.response(201, 'Success', annotation_collection_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(annotation_collection_model)
    def post(self):
        # prefer = interpret_header(request.headers)
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection = annotation_store.create_collection_es(collection_data, params)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view(), 201

    @auth.login_required
    @api.response(200, 'Success', collection_list_model)
    @api.response(404, 'Annotation Error', response_model)
    def get(self):
        params = get_params(request)
        response_data = []
        collection_data = annotation_store.get_collections_es(params)
        for collection in collection_data["collections"]:
            collection_url = request.url + "/" + collection["id"] + "/annotations/"
            container = AnnotationContainer(collection_url, collection, view=params["view"])
            response_data.append(container.view())
        return response_data


@api.route("/collections/<collection_id>")
class CollectionAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def get(self, collection_id):
        params = get_params(request)
        collection = annotation_store.get_collection_es(collection_id, params)
        if params["view"] == "PreferContainedDescriptions":
            collection["items"] = annotation_store.get_annotations_by_id_es(collection["items"], params)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    @api.response(201, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(annotation_collection_model)
    def put(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        if collection_data['id'] != collection_id:
            raise ValueError('updated collection has different id from id in request URL')
        collection = annotation_store.update_collection_es(collection_data)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    @api.response(204, 'Success', annotation_collection_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection = annotation_store.remove_collection_es(collection_id, params)
        return collection


@api.route("/collections/<collection_id>/annotations/")
class CollectionAnnotationsAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
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


@api.route("/collections/<collection_id>/annotations/<annotation_id>")
class CollectionAnnotationAPI(Resource):

    @auth.login_required
    @api.response(204, 'Success', annotation_collection_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, collection_id, annotation_id):
        params = get_params(request, anon_allowed=False)
        return annotation_store.remove_annotation_from_collection_es(annotation_id, collection_id, params)


"""--------------- User endpoints ------------------"""


@api.route("/users")
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
        return response, 200

    @auth.login_required
    @api.response(204, 'Success', user_response)
    def delete(self):
        user_store.delete_user(g.user)
        return {'message': 'user deleted'}, 204


@api.route("/login")
class LoginApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(400, 'Invalid user details received')
    @api.response(404, 'User does not exist')
    def post(self):
        if not g.user:
            # if no user object is POSTed, this is a bad request
            abort(400)
        token = user_store.generate_auth_token(g.user.user_id, expiration=600)
        return {"action": "authenticated", "user": {"username": g.user.username, "token": token.decode('ascii')}}, 200


@api.route("/logout")
class LogoutApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', user_response)
    @api.response(404, 'User does not exist')
    def get(self):
        # once token-based auth is implemented, remove token upon logout
        return {"action": "logged out"}, 200


"""--------------- IIIF endpoints ------------------"""


@api.route("/iiif_exchange/manifest/<resource_id>")
class IIIFExchangeManifestApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_list_response)
    @api.response(400, 'Invalid IIIF Exchange Manifest')
    def post(self, _resource_id):
        manifest = request.get_json()
        annotations = iiif_manifest.web_anno_from_manifest(manifest)
        return annotations, 200


@api.route("/iiif_exchange/resource/<resource_id>")
class IIIFExchangeResourceApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_list_response)
    @api.response(400, 'Invalid IIIF Exchange Manifest')
    def post(self, resource_id):
        annotations = annotation_store.get_from_index_by_target(resource_id)
        return annotations, 200


@api.route("/iiif_exchange/annotation/<annotation_id>")
class IIIFExchangeAnnotationApi(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_response)
    @api.response(404, 'Annotation does not exists')
    def get(self, annotation_id):
        try:
            annotation = annotation_store.get_from_index_by_id(annotation_id, "Annotation")
            annotation['id'] = 'http://localhost:3000/api/annotations/' + annotation['id']
            del annotation['target_list']
            annotation.pop('permissions', None)
            manifests = iiif_manifest.web_anno_to_manifest([annotation])
            print('manifests received')
            if isinstance(manifests, Manifest):
                response_data = manifests.to_json()
            else:
                response_data = [manifest.to_json() for manifest in manifests]
            print('manifests serialized')
            return response_data
        except PermissionError:
            return abort(404)

    @auth.login_required
    @api.response(200, 'Success', annotation_list_response)
    @api.response(400, 'Invalid IIIF Exchange Manifest')
    def post(self, _resource_id):
        manifest = request.get_json()
        annotations = iiif_manifest.web_anno_from_manifest(manifest)
        return annotations, 200


if __name__ == "__main__":
    swas_host = server_config["SWAServer"]["host"]
    swas_port = server_config["SWAServer"]["port"]
    app.run(host=swas_host, port=swas_port, debug=True, threaded=True)

