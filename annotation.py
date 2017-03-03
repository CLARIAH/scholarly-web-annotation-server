import json
import datetime
import pytz
import uuid
from rfc3987 import parse as parse_IRI
from collections import defaultdict

class AnnotationValidator(object):

    def validate(self, annotation):
        if type(annotation) != dict:
            print(type(annotation))
            raise InvalidAnnotation(message='annotation MUST be valid JSON')
        if "@context" not in annotation:
            raise InvalidAnnotation(message='annotation MUST have a @context')
        if annotation["@context"] != "http://www.w3.org/ns/anno.jsonld":
            raise InvalidAnnotation(message='annotation @context MUST include "http://www.w3.org/ns/anno.jsonld"')
        if 'type' not in annotation:
            raise InvalidAnnotation(message='annotation MUST have a type')
        if "Annotation" not in self.as_list(annotation['type']):
            raise InvalidAnnotation(message='annotation type MUST include "Annotation"')

        if 'target' not in annotation:
            raise InvalidAnnotation(message='annotation MUST have at least one target')
        for target in self.as_list(annotation['target']):
            target_id = None
            if type(target) == str: target_id = target
            elif type(target) == dict:
                if 'id' in target: target_id = target['id']
                elif 'source' in target: target_id = target['source']
            else:
                # there is no identifier for the target
                raise InvalidAnnotation(message='External annotation target MUST have an IRI identifier')
            try:
                # id must be an IRI
                parse_IRI(target_id, rule="IRI")
            except ValueError:
                raise InvalidAnnotation(message='annotation target id MUST be an IRI')
        return True

    def as_list(self, value):
        if type(value) == list:
            return value
        return [value]

class Annotation(object):

    def __init__(self, annotation):
        annotation['id'] = uuid.uuid4().urn
        annotation['created'] = datetime.datetime.now(pytz.utc).isoformat()
        self.validator = AnnotationValidator()
        self.validator.validate(annotation)
        self.type = self.determine_type(annotation)
        self.data = annotation
        self.id = annotation['id']

    def has_target(self, target_id):
        if not self.get_targets():
            return False
        for target in self.get_targets():
            if target == target_id:
                return True
            if 'id' in target['id'] == target_id:
                return True
            if 'selector' not in target or not target['selector'] or 'value' not in target['selector']:
                return False
            if target['selector']['value'] == target_id:
                return True
        return False

    def get_targets(self):
        if 'target' not in self.data:
            return []
        if type(self.data['target']) == list:
            return self.data['target']
        else:
            return [self.data['target']]

    def get_target_ids(self):
        return [self.get_target_id(target) for target in self.get_targets()]

    def get_target_id(self, target):
        if type(target) == str:
            return target
        if type(target) == dict:
            if 'id' in target:
                return target['id']
            return target['source']

    def update(self, updated_annotation):
        self.validator.validate(updated_annotation)
        if self.id == updated_annotation['id']:
            updated_annotation['modified'] = datetime.datetime.now(pytz.utc).isoformat()
            self.data = updated_annotation
        else:
            raise InvalidAnnotation(message="ID of updated annotation does not match ID of existing annotation")

    def determine_type(self, annotation):
        if 'target' not in annotation or 'body' not in annotation:
            return "enrichment"
        if 'conformsTo' not in annotation['body']:
            return "enrichment"
        if 'conformsTo' not in annotation['target']:
            return "enrichment"
        if annotation['target']['conformsTo'] != annotation['body']['conformsTo']:
            return "enrichment"
        if annotation['motivation'] != "linking":
            return "enrichment"
        return "structural"

    def get_type(self):
        return self.type

class AnnotationStore(object):

    def __init__(self, annotations=[]):
        self.index = {}
        self.target_index = defaultdict(list)
        for annotation in annotations:
            self.add(annotation)

    def add_bulk(self, annotations):
        added = []
        for annotation in annotations:
            added += [self.add(annotation)]
        return added

    def add(self, annotation):
        # make a new annotation object
        anno = Annotation(annotation)
        # do nothing if annotation already exists
        if self.exists(anno.id):
            return None
        # add annotation to index
        self.index[anno.id] = anno
        # add annotation targets to target_index
        for target_id in anno.get_target_ids():
            self.target_index[target_id] += [anno.id]
        return anno.data

    def get(self, annotation_id):
        try:
            return self.index[annotation_id].data
        except KeyError:
            raise AnnotationDoesNotExistError(annotation_id)

    def remove(self, annotation_id):
        annotation = self.get(annotation_id) # raises if not exists
        # first remove annotation from target_index
        for target_id in self.index[annotation_id].get_target_ids():
            self.target_index[target_id].remove(annotation_id)
            if self.target_index[target_id] == []:
                del self.target_index[target_id]
        # then remove from index
        del self.index[annotation_id]
        return annotation

    def update(self, updated_annotation):
        try:
            annotation = self.index[updated_annotation['id']]
            annotation.update(updated_annotation)
            return annotation.data
        except KeyError:
            raise AnnotationDoesNotExistError(updated_annotation['id'])

    def ids(self):
        return list(self.index.keys())

    def get_type(self, annotation_id):
        return self.index[annotation_id].type

    def get_by_target(self, target_id):
        annotations = []
        for anno_id in self.target_index[target_id]:
            anno = self.index[anno_id]
            if self.get_type(anno_id) == "structural":
                annotations += self.get_by_target(anno.data['body']['source'])
            annotations += [anno.data]
        return annotations

    def exists(self, annotation_id):
        if annotation_id in self.index:
            return True
        return False

    def list(self, ids=None):
        if not ids:
            ids = self.ids()
        return [annotation.data for id, annotation in self.index.items() if id in ids]

    def get_annotations_by_target(self, target):
        return self.target_index[target]

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

class AnnotationExistsError(Exception):
    status_code = 404

    def __init__(self, id, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = "There is already an annotation with ID %s" % (id)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

class AnnotationDoesNotExistError(Exception):
    status_code = 404

    def __init__(self, id, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = "There is no annotation with ID %s" % (id)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

if __name__ == "__main__":
    annotations_file = "data/annotations.json"
    try:
        with open(annotations_file, 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []

