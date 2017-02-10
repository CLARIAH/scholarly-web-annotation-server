
class Validation(object):

    def __init__(self, message="valid annotation", valid=False):
        self.message = message
        self.valid = valid

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

class AnnotationDoesNotExistError(Exception):
    status_code = 404

    def __init__(self, id, status_code=None, payload=None):
        Exception.__init__(self)
        print("NOT EXISTS: " + id)
        self.message = "There is no annotation with ID %s" % (id)
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

def validate_annotation(annotation):
    if type(annotation) != dict:
        return Validation(message='not valid JSON')
    if "@context" not in annotation:
        return Validation(message='annotation MUST have a @context')
    if annotation["@context"] != "http://www.w3.org/ns/anno.jsonld":
        return Validation(message='annotation MUST have @context: "http://www.w3.org/ns/anno.jsonld"')
    if 'type' not in annotation:
        return Validation(message='annotation must have a type')
    if "Annotation" not in get_value_as_list(annotation['type']):
        return Validation(message='annotation type MUST include "Annotation"')

    if 'target' not in annotation:
        return Validation(message='annotation MUST have at least one target')
    return Validation(valid=True)

def get_value_as_list(value):
    if type(value) == list:
        return value
    return [value]
