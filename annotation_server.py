import os
import json
from flask import Flask, Blueprint, request
from flask_restplus import Api, Resource

from models.annotation import AnnotationStore, AnnotationError
from models.resource import ResourceStore, ResourceError

app = Flask(__name__, static_url_path='', static_folder='public')
#cors = CORS(app)
#api = Api(app)
blueprint = Blueprint('api', __name__)
api = Api(blueprint)

annotation_store = AnnotationStore()
resource_store = None

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
    return error_to_dict(), error.status_code

@api.errorhandler(ResourceError)
def handle_invalid_resource(error):
    return error.to_dict(), error.status_code

@api.errorhandler(AnnotationError)
def handle_annotation_error(error):
    return error.to_dict(), error.status_code


@api.route("/api/annotations")
class HandleAnnotations(Resource):

    def get(self):
        return annotation_store.list()

    def post(self):
        new_annotation = request.get_json()
        response = annotation_store.add_annotation(new_annotation)
        save_annotations()
        return response

@api.route('/api/annotations/<annotation_id>')
class HandleAnnotation(Resource):

    def get(self, annotation_id):
        annotation = annotation_store.get(annotation_id)
        response_data = annotation
        return response_data

    def put(self, annotation_id):
        annotation = request.get_json()
        response_data = annotation_store.update(annotation)
        return response_data

    def delete(self, annotation_id):
        response_data = annotation_store.remove(annotation_id)
        return response_data

@api.route("/api/resources")
class HandleResources(Resource):

    def post(self):
        resource_map = request.get_json()
        return resource_store.register_by_map(resource_map)

    def get(self):
        return resource_store.get_resources()

@api.route("/api/resources/<resource_id>")
class HandleResource(Resource):

    def get(self, resource_id):
        return resource_store.get_resource(resource_id).json()

@api.route('/api/resources/<resource_id>/annotations')
class HandleResourceAnnotations(Resource):

    def get(self, resource_id):
        annotations = {}
        if resource_store.has_resource(resource_id):
            resource_ids = resource_store.get_resource(resource_id).list_members()
            annotations = annotation_store.get_by_targets(resource_ids)
        return annotations

@api.route('/api/resources/<resource_id>/structure')
class HandleResourceStructure(Resource):

    def get(self, resource_id):
        response = {}
        if resource_store.has_resource(resource_id):
            return resource_store.generate_resource_map(resource_id)
        else:
            raise ResourceError(message="unknown resource")

    def post(self, resource_id):
        resource_map = request.get_json()
        if resource_map["id"] != resource_id:
            raise ResourceError(message="resource id in map does not correspond with resource id in request URL")
        return resource_store.register_by_map(resource_map)

@api.route("/api/collections")
class HandleCollections(Resource):

    def post(self):
        collection_data = request.get_json()
        return annotation_store.create_collection(collection_data)

    def get(self):
        return annotation_store.retrieve_collections()

@api.route("/api/collections/<collection_id>")
class HandleCollection(Resource):

    def get(self, collection_id):
        return annotation_store.retrieve_collection(collection_id)

    def put(self, collection_id):
        data = request.get_json()
        return annotation_store.update_collection(collection_id, data)

    def delete(self, collection_id):
        return annotation_store.delete_collection(collection_id)

@api.route("/api/collections/<collection_id>/annotations/")
class HandleCollectionAnnotations(Resource):

    def post(self, collection_id):
        annotation_data = request.get_json()
        return annotation_store.add_annotation_to_collection(annotation_data, collection_id)
    def get(self, collection_id):
        return annotation_store.retrieve_collections()

@api.route("/api/collections/<collection_id>/annotations/<annotation_id>")
class HandleCollectionAnnotation(Resource):

    def get(self, collection_id, annotation_id):
        return annotation_store.get_annotation_from_collection(annotation_id, collection_id)

    def put(self, collection_id, annotation_id):
        return annotation_store.update_annotation_in_collection(annotation_data, collection_id)

    def delete(self, collection_id, annotation_id):
        return annotation_store.remove_annotation_from_collection(annotation_id, collection_id)

@api.route("/api/pages/<page_id>")
class HandlePage(Resource):

    def get(self, page_id):
        return annotation_store.retrieve_collection_page(page_id)

@api.route("/api/login")
class Login(Resource):

    def post(self):
        # dummy route for now, returns request data as is
        user_details = request.get_json()
        return user_details

def save_annotations():
    #annotation_store.save_annotations()
    with open(app.config['DATAFILE'], 'w') as f:
        f.write(json.dumps(annotation_store.list(), indent=4, separators=(',', ': ')))

def load_annotations():
    #annotation_store.load_annotations()
    try:
        with open(app.config['DATAFILE'], 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []
    annotation_store.add_bulk(annotations)

app.register_blueprint(blueprint)

if __name__ == "__main__":
    annotations_file = "data/annotations.json"
    app.config.update(DATAFILE=annotations_file)
    load_annotations()
    resource_config = {
        "resource_file": "data/resource.pickle",
        "triple_file": "data/vocabularies.ttl",
        "url_file": "data/vocabulary_refs.json"
    }
    annotation_config = {
        "collections_file": "data/annotation_collections.pickle",
        "pages_file": "data/annotation_pages.pickle",
        "annotations_file": "data/annotations.pickle"
    }
    annotation_store.configure(annotation_config)
    resource_store = ResourceStore(resource_config)
    app.run(port=int(os.environ.get("PORT", 5000)), debug=True, threaded=True)

