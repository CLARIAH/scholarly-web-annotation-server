
class Validation(object):

    def __init__(self, message="valid annotation", valid=True):
        self.message = message
        self.valid = valid

def validate_annotation(annotation):
    if type(annotation) != dict:
        return Validation(message='not valid JSON', valid=False)
    if "@context" not in annotation:
        return Validation(message='@context property missing', valid=False)
    if annotation["@context"] != "http://www.w3.org/ns/anno.jsonld":
        return Validation(message='annotation must have @context: "http://www.w3.org/ns/anno.jsonld"', valid=False)
    return Validation()
