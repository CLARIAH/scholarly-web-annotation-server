from typing import Dict, Union
from flask import Flask, Blueprint, request, abort, make_response, jsonify, g, json
from flask_restx import Namespace, Resource, fields
from parse.headers_params import get_params
from models.user_store import UserStore
from models.annotation_store import AnnotationStore
from models.annotation_container import AnnotationContainer
from settings import server_config
from flask_httpauth import HTTPBasicAuth

namespace = 'collections'
api_url = server_config['SWAServer']['url'] + server_config['SWAServer']['api_prefix']
annotation_store = AnnotationStore(server_config["Elasticsearch"])
user_store = UserStore(server_config["Elasticsearch"])
api = Namespace(namespace, description='Annotation Collection related operations')
auth = HTTPBasicAuth()

# generic response model
response_model = api.model("Response", {
    "status": fields.String(description="Status", required=True, enum=["success", "error"]),
    "message": fields.String(description="Message from server", required=True),
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


@auth.verify_password
def verify_password(token_or_username, password):
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


# Update configuration
def configure_store(config: Dict[str, Union[str, int]]):
    annotation_store.configure(config)
    user_store.configure(config)


def make_external_id(annotation_id: str) -> str:
    """Turn a full external id with API URL into an internal id without API URL."""
    return f"{api_url}/{namespace}/{annotation_id}"


def make_internal_id(annotation_id: str) -> str:
    """Turn an internal id without API URL into a full external id with API URL."""
    return annotation_id.split('/')[-1]


"""--------------- Collection endpoints ------------------"""


@api.route("/")
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
        collection['id'] = make_external_id(collection['id'])
        container = AnnotationContainer(request.base_url, collection, view=params["view"])
        return container.view(), 201

    @auth.login_required
    @api.response(200, 'Success', collection_list_model)
    @api.response(404, 'Annotation Error', response_model)
    def get(self):
        params = get_params(request)
        response_data = []
        collection_data = annotation_store.get_collections_es(params)
        for collection in collection_data["collections"]:
            collection['id'] = make_external_id(collection['id'])
            # collection_url = collection["id"] + "/annotations/"
            container = AnnotationContainer(request.base_url, collection, view=params["view"])
            response_data.append(container.view())
        return response_data


@api.route("/<collection_id>")
class CollectionAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def get(self, collection_id):
        params = get_params(request)
        collection = annotation_store.get_collection_es(collection_id, params)
        collection['id'] = make_external_id(collection['id'])
        if params["view"] == "PreferContainedDescriptions":
            collection["items"] = annotation_store.get_annotations_by_id_es(collection["items"], params)
        container = AnnotationContainer(request.base_url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    @api.response(201, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(annotation_collection_model)
    def put(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection_data = request.get_json()
        collection_data['id'] = make_internal_id(collection_data['id'])
        if collection_data['id'] != collection_id:
            raise ValueError('updated collection has different id from id in request URL')
        collection = annotation_store.update_collection_es(collection_data)
        collection['id'] = make_external_id(collection['id'])
        container = AnnotationContainer(request.base_url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    @api.response(204, 'Success', annotation_collection_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, collection_id):
        params = get_params(request, anon_allowed=False)
        collection = annotation_store.remove_collection_es(collection_id, params)
        collection['id'] = make_external_id(collection['id'])
        return collection


@api.route("/<collection_id>/annotations/")
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
        else:
            annotation_data['id'] = make_internal_id(annotation_data['id'])
        collection = annotation_store.add_annotation_to_collection_es(annotation_data['id'], collection_id, params)
        collection['id'] = make_external_id(collection['id'])
        container = AnnotationContainer(request.base_url, collection, view=params["view"])
        return container.view()

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def get(self, collection_id):
        params = get_params(request)
        collection = annotation_store.get_collection_es(collection_id, params)
        if params["view"] == "PreferContainedDescriptions" or ("iris" in params and params["iris"] == 0):
            annotations = annotation_store.get_annotations_by_id_es(collection["items"], params)
            collection["items"] = annotations
        container = AnnotationContainer(request.base_url, collection["items"], view=params["view"])
        return container.view()


@api.route("/<collection_id>/annotations/<annotation_id>")
class CollectionAnnotationAPI(Resource):

    @auth.login_required
    @api.response(204, 'Success', annotation_collection_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, collection_id, annotation_id):
        params = get_params(request, anon_allowed=False)
        return annotation_store.remove_annotation_from_collection_es(annotation_id, collection_id, params)
