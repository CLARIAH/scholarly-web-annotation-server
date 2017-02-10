# This file provided by Facebook is for non-commercial testing and evaluation
# purposes only. Facebook reserves all rights not expressly granted.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# FACEBOOK BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import uuid
import time
import json
import os
#import requests
import xmltodict
import re
from annotation import validate_annotation
from flask import Flask, Response, request
from flask import jsonify

app = Flask(__name__, static_url_path='', static_folder='public')
app.add_url_rule('/', 'root', lambda: app.send_static_file('testletter.html'))

class InvalidAnnotation(Exception):
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

def make_response(response_data):
    return Response(
        json.dumps(response_data),
        mimetype='application/json',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*'
        }
    )

def is_target(annotation, target_id):
    targets = get_targets(annotation)
    if not targets:
        return False
    for target in targets:
        if target['source'] == target_id:
            return True
        if 'selector' not in target or not target['selector'] or 'value' not in target['selector']:
            return False
        if target['selector']['value'] == target_id:
            return True
    return False

def get_targets(annotation):
    if 'target' not in annotation:
        return []
    if type(annotation['target']) == dict:
        return [annotation['target']]
    else:
        return annotation['target']

def resource_is_subresource(resource_id, annotation):
    if 'body' not in annotation or type(annotation['body']) != dict:
        return False
    if annotation['body']['source'] != resource_id:
        return False
    if annotation['motivation'] != "linking":
        return False
    if annotation['body']['conformsTo'] != annotation['target']['conformsTo']:
        return False
    return True

def resource_has_subresource(resource_id, annotation):
    if 'target' not in annotation or type(annotation['target']) != dict:
        return False
    if annotation['target']['source'] != resource_id:
        return False
    if annotation['motivation'] != "linking":
        return False
    if annotation['target']['conformsTo'] != annotation['body']['conformsTo']:
        return False
    return True

def get_superresource_relations(resource_id, annotations):
    relations = []
    for annotation in annotations:
        if resource_is_subresource(resource_id, annotation):
            relations += [annotation]
            relations += get_superresource_relations(annotation['target']['source'], annotations)
    return relations

def get_subresource_relations(resource_id, annotations):
    relations = []
    for annotation in annotations:
        if resource_has_subresource(resource_id, annotation):
            relations += [annotation]
            relations += get_subresource_relations(annotation['body']['source'], annotations)
    return relations

def get_resource_ids(target_annotations):
    resource_ids = []
    for annotation in target_annotations:
        resource_ids.append(annotation['target']['source'])
        resource_ids.append(annotation['body']['source'])
    return resource_ids

def add_annotations_on_annotations(stored_annotations, target_annotations):
    curr_ids = [target_annotation['id'] for target_annotation in target_annotations]
    new_ids = []
    new_annotations = []
    for annotation in stored_annotations:
        if annotation['id'] in curr_ids: continue
        target_ids = []
        for target in get_targets(annotation):
            target_ids += [target['source']]
        for target_id in target_ids:
            if target_id in curr_ids:
                if annotation['id'] not in curr_ids and annotation['id'] not in new_ids:
                    new_ids += [annotation['id']]
                    new_annotations += [annotation]

    if len(new_ids) > 0:
        target_annotations += new_annotations
        return False
    else:
        return True

def update_annotation(annotations, updated_annotation):
    updated_annotation['modified'] = int(time.time())
    for index, annotation in enumerate(annotations):
        if annotation['id'] == updated_annotation['id']:
            annotations.remove(annotation)
            annotations.insert(index, updated_annotation)

@app.errorhandler(InvalidAnnotation)
def handle_invalid_annotation(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response

@app.route('/api/annotations/target/<target_id>', methods=['GET'])
def get_annotations_by_target(target_id):
    annotations_file = "data/annotations.json"
    print("GET annotations by target id %s" % (target_id))
    try:
        with open(annotations_file, 'r') as f:
            stored_annotations = json.loads(f.read())
    except FileNotFoundError:
        stored_annotations = []

    target_annotations = get_subresource_relations(target_id, stored_annotations)
    resource_ids = get_resource_ids(target_annotations)

    for resource_id in resource_ids:
        for annotation in stored_annotations:
            if annotation in target_annotations:
                continue
            if is_target(annotation, resource_id):
                target_annotations += [annotation]

    done = False
    while not done:
        done = add_annotations_on_annotations(stored_annotations, target_annotations)
    #print(json.dumps(target_annotations, indent=4))

    return make_response(target_annotations)

@app.route('/api/annotations/annotation/<annotation_id>', methods=['GET', 'PUT', 'DELETE'])
def get_annotation_by_id(annotation_id):
    annotations_file = "data/annotations.json"
    try:
        with open(annotations_file, 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []

    response_data = annotations

    for index, annotation in enumerate(annotations):
        if annotation['id'] == annotation_id:
            if request.method == 'GET':
                response_data = annotation
            if request.method == 'PUT':
                edited_annotation = request.get_json()
                update_annotation(annotations, edited_annotation)
                response_data = edited_annotation
                print("updating annotation")
            if request.method == 'DELETE':
                annotations.remove(annotation)
                print("removing annotation")

    with open(annotations_file, 'w') as f:
        f.write(json.dumps(annotations, indent=4, separators=(',', ': ')))

    return make_response(response_data)

@app.route('/api/annotations', methods=['GET', 'POST'])
def get_annotations():
    annotations_file = "data/annotations.json"
    try:
        with open(annotations_file, 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []

    if request.method == 'POST':
        new_annotation = request.get_json()
        validation = validate_annotation(new_annotation)
        if validation.valid == False:
            raise InvalidAnnotation(validation.message, status_code=400)
        new_annotation['id'] = uuid.uuid4().urn
        new_annotation['created'] = int(time.time())
        annotations.append(new_annotation)
        response_data = new_annotation

        with open(annotations_file, 'w') as f:
            f.write(json.dumps(annotations, indent=4, separators=(',', ': ')))

    if request.method == "GET":
        response_data = annotations

    return make_response(response_data)

@app.route("/api/login", methods=["POST"])
def login():
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

if __name__ == '__main__':
    app.run(port=int(os.environ.get("PORT", 3000)), debug=True)
