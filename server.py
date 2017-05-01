# File: annotation_server.py
# Created by: Marijn Koolen (https://github.com/marijnkoolen)
# Repository: https://github.com/marijnkoolen/rdfa-annotation-client
# Description:  this is a temporary solution for an annotation server
#               for the RDFa Annotation Client. For a proper solution,
#               look at https://huygensing.github.io/alexandria

import json
import os
#import requests
import xmltodict
import re
from server_models.annotation import InvalidAnnotation, AnnotationDoesNotExistError, AnnotationStore
from server_models.resource import ResourceStore, ResourceError
from flask import Flask, Response, request
from flask import jsonify
from flask.ext.cors import CORS

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('testletter.html'))
cors = CORS(app)
annotation_store = AnnotationStore()
resource_store = None

def make_response(response_data):
    return Response(
        json.dumps(response_data),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

def generic_error_handler(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(ResourceError)
def handle_invalid_resource(error):
    return generic_error_handler(error)

@app.errorhandler(AnnotationDoesNotExistError)
def handle_no_such_annotation(error):
    return generic_error_handler(error)

@app.errorhandler(InvalidAnnotation)
def handle_invalid_annotation(error):
    return generic_error_handler(error)

@app.route('/api/annotations/target/<target_id>', methods=['GET'])
def get_annotations_by_target(target_id):
    annotations = annotation_store.get_by_target(target_id)
    return make_response(annotations)

@app.route('/api/annotations/annotation/<annotation_id>', methods=['GET', 'PUT', 'DELETE'])
def get_annotation_by_id(annotation_id):
    response_data = None

    annotation = annotation_store.get(annotation_id)
    if not annotation:
        raise AnnotationDoesNotExistError(annotation_id, status_code=404)
    if request.method == 'GET':
        response_data = annotation
    if request.method == 'PUT':
        annotation = request.get_json()
        response_data = annotation_store.update(annotation)
    if request.method == 'DELETE':
        response_data = annotation_store.remove(annotation_id)
    save_annotations()
    return make_response(response_data)

@app.route("/api/annotations", methods=["GET", "POST"])
def get_annotations():
    if request.method == "GET":
        response = annotation_store.list()
    elif request.method == "POST":
        new_annotation = request.get_json()
        response = annotation_store.add_annotation(new_annotation)
        save_annotations()
    return make_response(response)

@app.route("/api/login", methods=["POST"])
def login():
    # dummy route for now
    # returns request data as is
    user_details = request.get_json()
    return make_response(user_details)

@app.route('/api/resources/<resource_id>/annotations', methods=['GET'])
def get_resource_annotations(resource_id):
    annotations = {}
    if resource_store.has_resource(resource_id):
        resource_ids = resource_store.get_resource(resource_id).list_members()
        annotations = annotation_store.get_by_targets(resource_ids)
    return make_response(annotations)

@app.route('/api/resources/<resource_id>/structure', methods=['GET', 'POST'])
def get_resource_structure(resource_id):
    response = {}
    if request.method == "POST":
        resource_map = request.get_json()
        if resource_map["id"] != resource_id:
            raise ResourceError(message="resource id in map does not correspond with resource id in request URL")
        response = resource_store.register_by_map(resource_map)
    if request.method == "GET":
        if resource_store.has_resource(resource_id):
            response = resource_store.generate_resource_map(resource_id)
        else:
            raise ResourceError(message="unknown resource")
    return make_response(response)

@app.route("/api/resource/<resource_id>/data/<format>")
def get_resource(resource_id, format):
    fname = "data/%s.xml" % (resource_id)
    with open (fname, 'rt') as fh:
        resource_data = fh.read()

    if format == "json":
        xml_string = re.sub("<\?xml.*?\?>", "", resource_data)
        json_data = xmltodict.parse(xml_string, process_namespaces=False)
        return make_response(json_data)
    else:
        return resource_data

@app.route("/api/resources/<resource_id>", methods=["GET", "PUT", "DELETE"])
def handle_known_resource(resource_id):
    response = {}
    if not resource_store.has_resource(resource_id):
        raise ResourceError(message="unknown resource")
    # TO DO: return basic resource info similar to Alexandria response
    if request.method == "GET":
        response = resource_store.get_resource(resource_id).json()
    return make_response(response)

@app.route("/api/resources", methods=["POST"])
def register_resource():
    resource_map = request.get_json()
    response = resource_store.register_by_map(resource_map)
    return make_response(response)

def save_annotations():
    with open(app.config['DATAFILE'], 'w') as f:
        f.write(json.dumps(annotation_store.list(), indent=4, separators=(',', ': ')))

def load_annotations():
    try:
        with open(app.config['DATAFILE'], 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []
    annotation_store.add_bulk(annotations)

if __name__ == '__main__':
    annotations_file = "data/annotations.json"
    app.config.update(DATAFILE=annotations_file)
    load_annotations()
    resource_config = {
        "resource_file": "data/resource.pickle",
        "triple_file": "data/vocabularies.ttl",
        "url_file": "data/vocabulary_refs.json"
    }
    resource_store = ResourceStore(resource_config)
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True, threaded=True)

