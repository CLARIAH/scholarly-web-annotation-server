from typing import Dict, Union
from flask import request, abort, jsonify, make_response, g
from flask_restx import Namespace, Resource, fields
from parse.headers_params import get_params
from models.annotation_store import AnnotationStore
from models.user_store import UserStore
from models.annotation_container import AnnotationContainer
from settings import server_config
from flask_httpauth import HTTPBasicAuth

namespace = 'annotations'
api_url = server_config['SWAServer']['url'] + server_config['SWAServer']['api_prefix']
annotation_store = AnnotationStore(server_config["Elasticsearch"])
user_store = UserStore(server_config["Elasticsearch"])
api = Namespace(namespace, description='Annotation related operations')
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


"""--------------- Annotation endpoints ------------------"""


annotation_parameters = {
    'iris': 'Integer: 0 (show full annotations) or 1 (show only IRIs)',
    'access_status': 'access and permission status: "private", "public"',
    'target_id': 'annotation target id: only retrieve annotations targeting a specific id',
    'target_type': 'annotation target type: only retrieve annotations targeting a specific type'
}


@api.doc(params=annotation_parameters, required=False)
@api.route("/", endpoint='annotation_list')
class AnnotationsAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', container_model)
    @api.response(404, 'Annotation Error', response_model)
    def get(self):
        params = get_params(request)
        data = annotation_store.get_annotations_es(params)
        # print('ANNOTATION API - request.url:', request.url)
        # print('ANNOTATION API - request.base_url:', request.base_url)
        # print('ANNOTATION API - request.url_root:', request.url_root)
        container = AnnotationContainer(request.base_url, data["annotations"],
                                        view=params["view"], total=data["total"])
        return container.view()

    @auth.login_required
    @api.response(201, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    @api.expect(annotation_model)
    def post(self):
        params = get_params(request, anon_allowed=False)
        new_annotation = request.get_json()
        annotation = annotation_store.add_annotation_es(new_annotation, params=params)
        annotation['id'] = make_external_id(annotation['id'])
        return annotation, 201


@api.doc(params={'annotation_id': '<annotation_uuid>'}, required=False)
@api.route('/<annotation_id>', endpoint='annotation')
class AnnotationAPI(Resource):

    @auth.login_required
    @api.response(200, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Annotation does not exist', response_model)
    def get(self, annotation_id):
        params = get_params(request)
        try:
            annotation = annotation_store.get_annotation_es(annotation_id, params)
            annotation['id'] = make_external_id(annotation['id'])
            return annotation
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
        annotation['id'] = make_internal_id(annotation['id'])
        if annotation['id'] != annotation_id:
            raise ValueError('updated annotation has different id from id in request URL')
        updated_annotation = annotation_store.update_annotation_es(annotation, params=params)
        updated_annotation['id'] = make_external_id(updated_annotation['id'])
        return updated_annotation

    @auth.login_required
    @api.response(204, 'Success', annotation_model)
    @api.response(403, 'Invalid Annotation Error', response_model)
    @api.response(404, 'Invalid Annotation Error', response_model)
    def delete(self, annotation_id):
        params = get_params(request, anon_allowed=False)
        annotation = annotation_store.remove_annotation_es(annotation_id, params)
        annotation['id'] = make_external_id(annotation['id'])
        return annotation
