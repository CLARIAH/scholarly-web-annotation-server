# File: annotation_server.py
# Created by: Marijn Koolen (https://github.com/marijnkoolen)
# Description:  this is a temporary solution for an annotation server
#               for the RDFa Annotation Client. For a proper solution,
#               look at https://huygensing.github.io/alexandria

import json
import os
#import requests
import xmltodict
import re
from server.annotation import InvalidAnnotation, AnnotationDoesNotExistError
from server.annotation import AnnotationStore
from flask import Flask, Response, request
from flask import jsonify

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('testletter.html'))
store = AnnotationStore()

def make_response(response_data):
    return Response(
        json.dumps(response_data),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

@app.errorhandler(AnnotationDoesNotExistError)
def handle_no_such_annotation(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.errorhandler(InvalidAnnotation)
def handle_invalid_annotation(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/api/annotations/target/<target_id>', methods=['GET'])
def get_annotations_by_target(target_id):
    print("GET annotations by target id %s" % (target_id))
    annotations = store.get_by_target(target_id)
    return make_response(annotations)

@app.route('/api/annotations/annotation/<annotation_id>', methods=['GET', 'PUT', 'DELETE'])
def get_annotation_by_id(annotation_id):
    response_data = None

    annotation = store.get(annotation_id)
    if not annotation:
        raise AnnotationDoesNotExistError(annotation_id, status_code=404)
    if request.method == 'GET':
        response_data = annotation
    if request.method == 'PUT':
        annotation = request.get_json()
        response_data = store.update(annotation)
    if request.method == 'DELETE':
        response_data = store.remove(annotation_id)
    save_annotations()
    return make_response(response_data)

@app.route('/api/annotation', methods=['POST'])
def post_annotation():
    new_annotation = request.get_json()
    stored_annotation = store.add(new_annotation)
    save_annotations()
    return make_response(stored_annotation)

@app.route('/api/annotations', methods=['GET'])
def get_annotations():
    annotations = store.list()
    return make_response(annotations)

@app.route("/api/login", methods=["POST"])
def login():
    # dummy route for now
    # returns request data as is
    user_details = request.get_json()
    return make_response(user_details)

@app.route("/api/resource/<resource_id>/<format>")
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
    if request.method == "GET":
        response = {}
    return make_response(response)

@app.route("/api/resources", methods=["POST"])
def register_resource():
    resource_map = request.get_json()
    print(json.dumps(resource_map, indent=4))
    return make_response(resource_map)

def save_annotations():
    with open(app.config['DATAFILE'], 'w') as f:
        f.write(json.dumps(store.list(), indent=4, separators=(',', ': ')))

def load_annotations():
    try:
        with open(app.config['DATAFILE'], 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []
    store.add_bulk(annotations)

if __name__ == '__main__':
    annotations_file = "data/annotations.json"
    app.config.update(DATAFILE=annotations_file)
    load_annotations()
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)

