import json
import datetime
import pytz
import uuid
from rfc3987 import parse as parse_IRI

class WebAnnotationValidator(object):

    def __init__(self):
        self.accepted_types = ["Annotation", "AnnotationCollection", "AnnotationPage"]

    def validate(self, annotation, annotation_type=None):
        self.validate_generic(annotation)
        self.validate_type(annotation, annotation_type)
        return True

    def validate_generic(self, annotation):
        if type(annotation) != dict:
            raise AnnotationError(message='annotation MUST be valid JSON')
        if "@context" not in annotation:
            raise AnnotationError(message='annotation MUST have a @context')
        if annotation["@context"] != "http://www.w3.org/ns/anno.jsonld":
            raise AnnotationError(message='annotation @context MUST include "http://www.w3.org/ns/anno.jsonld"')
        if 'type' not in annotation:
            raise AnnotationError(message='annotation MUST have a type')

    def validate_type(self, annotation, annotation_type):
        anno_type = self.has_valid_type(annotation)
        if annotation_type == None:
            annotation_type = anno_type
        if annotation_type not in self.as_list(annotation['type']):
            raise AnnotationError(message="annotation is not of type %s" % (annotation_type))
        if annotation_type == "Annotation":
            self.validate_annotation(annotation)
        if annotation_type == "AnnotationPage":
            self.validate_annotation_page(annotation)
        if annotation_type == "AnnotationCollection":
            self.validate_annotation_collection(annotation)

    def validate_annotation_collection(self, annotation_collection):
        if "AnnotationCollection" not in self.as_list(annotation_collection['type']):
            raise AnnotationError(message='annotation "type" property MUST include "AnnotationCollection"')
        if "label" not in annotation_collection.keys():
            raise AnnotationError(message='annotation collection MUST have an "label" property with as value a string.')
        if type(annotation_collection["label"]) != str:
            raise AnnotationError(message='annotation collection "label" property MUST be a string.')
        if "total" in annotation_collection.keys():
            if "first" not in annotation_collection.keys():
                raise AnnotationError(message='Non-empty collection MUST have "first" property referencing the first AnnotationPage')
            if "last" not in annotation_collection.keys():
                raise AnnotationError(message='Non-empty collection MUST have "last" property referencing the first AnnotationPage')

    def validate_annotation_page(self, annotation_page):
        if "AnnotationPage" not in self.as_list(annotation_page['type']):
            raise AnnotationError(message='annotation "type" property MUST include "AnnotationPage"')
        if "items" not in annotation_page.keys():
            raise AnnotationError(message='annotation page MUST have an "items" property with as value a list with at least one annotation.')
        if type(annotation_page["items"]) != list or len(annotation_page["items"]) == 0:
            raise AnnotationError(message='annotation page "items" property MUST be a list with at least one annotation.')

    def validate_annotation(self, annotation):
        if "Annotation" not in self.as_list(annotation['type']):
            raise AnnotationError(message='annotation type MUST include "Annotation"')

        if 'target' not in annotation:
            raise AnnotationError(message='annotation MUST have at least one target')
        for target in self.as_list(annotation['target']):
            target_id = None
            if type(target) == str: target_id = target
            elif type(target) == dict:
                if 'id' in target: target_id = target['id']
                elif 'source' in target: target_id = target['source']
            else:
                # there is no identifier for the target
                raise AnnotationError(message='External annotation target MUST have an IRI identifier')
            try:
                # id must be an IRI
                parse_IRI(target_id, rule="IRI")
            except ValueError:
                raise AnnotationError(message='annotation target id MUST be an IRI')

    def has_valid_type(self, annotation):
        types = [anno_type for anno_type in self.as_list(annotation["type"]) if anno_type in self.accepted_types]
        if len(types) > 1:
            raise AnnotationError(message="annotation cannot have multiple annotation types")
        if len(types) == 0:
            raise AnnotationError(message='annotation type MUST be one of "Annotation", "AnnotationCollection", "AnnotationPage"')
        return types[0]

    def as_list(self, value):
        if type(value) == list:
            return value
        return [value]

class Annotation(object):

    def __init__(self, annotation):
        if 'id' not in annotation:
            annotation['id'] = uuid.uuid4().urn
        if 'created' not in annotation:
            annotation['created'] = datetime.datetime.now(pytz.utc).isoformat()
        self.validator = WebAnnotationValidator()
        self.validator.validate(annotation)
        self.data = annotation
        self.id = annotation['id']
        self.in_collection = []

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
            raise AnnotationError(message="ID of updated annotation does not match ID of existing annotation")

    def add_collection(self, collection_id):
        if collection_id not in self.in_collection:
            self.in_collection.append(collection_id)

    def remove_collection(self, collection_id):
        if collection_id in self.in_collection:
            self.in_collection.remove(collection_id)

class AnnotationError(Exception):
    status_code = 404

    def __init__(self, message, status_code=404, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

if __name__ == "__main__":
    annotations_file = "data/annotations.json"
    try:
        with open(annotations_file, 'r') as f:
            annotations = json.loads(f.read())
    except FileNotFoundError:
        annotations = []

