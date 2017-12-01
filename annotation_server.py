import os
from flask import Flask, Blueprint, request
from flask_restplus import Api, Resource, fields
from flask.ext.cors import CORS

from models.annotation_store import AnnotationStore
from models.annotation import AnnotationError
from models.annotation_container import AnnotationContainer

app = Flask(__name__, static_url_path='', static_folder='public')
cors = CORS(app)
#api = Api(app)
blueprint = Blueprint('api', __name__)
api = Api(blueprint)

annotation_store = AnnotationStore()

"""--------------- Error handling ------------------"""

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
            self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.to_dict(), error.status_code

@api.errorhandler(AnnotationError)
def handle_annotation_error(error):
    return error.to_dict(), error.status_code



"""--------------- API request and response models ------------------"""

#generic response model
response_model = api.model('Response', {
    'status': fields.String(description='Status', required=True, enum=['success', 'error']),
    'message': fields.String(description='Message from server', required=True),
})

target_model = api.schema_model('AnnotationTarget', {
    'properties': {
        'id': {
            'type': 'string'
        },
        'type': {
            'type': 'string'
        },
        'language': {
            'type': 'string'
        },
    }
})

body_model = api.schema_model('AnnotationBody', {
    'properties': {
        'id': {
            'type': 'string'
        },
        'type': {
            'type': 'string'
        },
        'created': {
            'type': 'string',
            'format': 'date-time'
        },
        'purpose': {
            'type': 'string'
        },
        'value': {
            'type': 'string'
        },
    },
    'type': 'object'
})

annotation_model = api.model('Annotation', {
    '@context': fields.String(description="The context that determines the meaning of the JSON as an Annotation", required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    'id': fields.String(description='Annotation ID', required=False),
    'type': fields.String(description="Annotation Type", required=True, enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    'creator': fields.String(description="Annotation Creator", required=False),
    'body': fields.List(fields.Nested(body_model))
})

annotation_response = api.clone('AnnotationResponse', response_model, {'annotation': fields.Nested(annotation_model)})

annotation_list_response = api.clone('AnnotationListResponse', response_model, {
    'annotations': fields.List(fields.Nested(annotation_model), description="List of annotations")
})

def parse_prefer_header(data):
    parsed = {}
    for part in data.strip().split(';'):
        key, value = part.split('=')
        parsed[key] = value.strip('"')
    return parsed

def interpret_header(headers):
    params = {
        "view": "PreferMinimalContainer"
    }
    if headers.get('Prefer'):
        parsed = parse_prefer_header(headers.get('Prefer'))
        if 'return' in parsed and parsed['return'] == 'representation':
            params['view'] = parsed['include'].split('#')[1]
    return params

def parse_query_parameters(request, params):
    params["page"] = 0
    page = request.args.get('page')
    if page != None:
        params["page "]= int(page)
        params["view"] = "PreferContainedIRIs"
    iris = request.args.get('iris')
    if iris != None:
        params["iris"] = int(iris)
        if params["iris"] == 0:
            params["view"] = "PreferContainedDescriptions"

"""--------------- Annotation endpoints ------------------"""


@api.route("/api/annotations", endpoint='annotation_list')
class AnnotationsAPI(Resource):

    @api.response(200, 'Success', annotation_list_response)
    @api.response(404, 'Annotation Error')
    def get(self):
        params = interpret_header(request.headers)
        parse_query_parameters(request, params)
        data = annotation_store.get_annotations_es(page=params["page"])
        container = AnnotationContainer(request.url, data["annotations"], view=params["view"], total=data["total"])
        return container.view()

    @api.response(200, 'Success')
    @api.response(404, 'Invalid Annotation Error')
    @api.expect(annotation_model)
    def post(self):
        new_annotation = request.get_json()
        response = annotation_store.add_annotation_es(new_annotation)
        return response

@api.doc(params={'annotation_id': 'The annotation ID'}, required=False)
@api.route('/api/annotations/<annotation_id>', endpoint='annotation')
class AnnotationAPI(Resource):

    @api.response(200, 'Success', annotation_response)
    @api.response(404, 'Annotation does not exist')
    def get(self, annotation_id):
        annotation = annotation_store.get_annotation_es(annotation_id)
        response_data = annotation
        return response_data

    def put(self, annotation_id):
        annotation = request.get_json()
        response_data = annotation_store.update_annotation_es(annotation)
        return response_data

    def delete(self, annotation_id):
        response_data = annotation_store.remove_annotation_es(annotation_id)
        return response_data


"""--------------- Resource endpoints ------------------"""

@api.route('/api/resources/<resource_id>/annotations')
class ResourceAnnotationsAPI(Resource):

    def get(self, resource_id):
        annotations = []
        annotations = annotation_store.get_annotations_by_target_es({"id": resource_id})
        for annotation in annotations:
            print(annotation)
        return annotations

"""--------------- Collection endpoints ------------------"""


@api.route("/api/collections")
class CollectionsAPI(Resource):

    def post(self):
        prefer = interpret_header(request.headers)
        collection_data = request.get_json()
        collection = annotation_store.create_collection_es(collection_data)
        container = AnnotationContainer(request.url, collection, view=prefer["view"])
        return container.view()

    def get(self):
        prefer = interpret_header(request.headers)
        response_data = []
        for collection in  annotation_store.get_collections_es():
            container = AnnotationContainer(request.url, collection, view=prefer["view"])
            response_data.append(container.view())
        return response_data

@api.route("/api/collections/<collection_id>")
class CollectionAPI(Resource):

    def get(self, collection_id):
        params = interpret_header(request.headers)
        collection = annotation_store.get_collection_es(collection_id)
        if params["view"] == "PreferContainedDescriptions":
            collection["items"] = annotation_store.get_annotations_by_id_es(collection["items"])
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    def put(self, collection_id):
        params = interpret_header(request.headers)
        collection_data = request.get_json()
        collection = annotation_store.update_collection_es(collection_data)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    def delete(self, collection_id):
        #params = interpret_header(request.headers)
        collection = annotation_store.remove_collection_es(collection_id)
        #container = AnnotationContainer(request.url, collection, view=params["view"])
        #return container.view()
        return collection

@api.route("/api/collections/<collection_id>/annotations/")
class CollectionAnnotationsAPI(Resource):

    @api.response(200, 'Success')
    @api.response(404, 'Invalid Annotation Error')
    @api.expect(annotation_model)
    def post(self, collection_id):
        params = interpret_header(request.headers)
        annotation_data = request.get_json()
        if 'id' not in annotation_data.keys():
            annotation_data = annotation_store.add_annotation_es(annotation_data)
        collection = annotation_store.add_annotation_to_collection_es(annotation_data['id'], collection_id)
        container = AnnotationContainer(request.url, collection, view=params["view"])
        return container.view()

    def get(self, collection_id):
        params = interpret_header(request.headers)
        collection = annotation_store.get_collection_es(collection_id)
        container = AnnotationContainer(request.url, collection.items, view=params["view"])
        return container.view()

@api.route("/api/collections/<collection_id>/annotations/<annotation_id>")
class CollectionAnnotationAPI(Resource):

    def get(self, collection_id, annotation_id):
        return annotation_store.get_annotation_from_collection_es(annotation_id, collection_id)

    def put(self, collection_id, annotation_id):
        annotation_data = request.get_json()
        if annotation_data["id"] != annotation_id:
            raise AnnotationError(message="annotation id in annotation data does not correspond with annotation id in request URL")
        return annotation_store.update_annotation_es(annotation_data)

    def delete(self, collection_id, annotation_id):
        return annotation_store.remove_annotation_from_collection_es(annotation_id, collection_id)

@api.route("/api/pages/<page_id>")
class PageAPI(Resource):

    def get(self, page_id):
        return annotation_store.retrieve_collection_page(page_id)

@api.route("/api/login")
class LoginAPI(Resource):

    def post(self):
        # dummy route for now, returns request data as is
        user_details = request.get_json()
        return user_details

app.register_blueprint(blueprint)

if __name__ == "__main__":
    annotations_file = "data/annotations.json"
    app.config.update(DATAFILE=annotations_file)
    annotation_config = {
        "Elasticsearch": {
            "host": "localhost",
            "port": 9200,
            "index": "swa",
            "page_size": 1000
        }
    }
    annotation_store.configure_index(annotation_config["Elasticsearch"])
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True, threaded=True)

