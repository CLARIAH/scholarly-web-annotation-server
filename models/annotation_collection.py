import uuid
import datetime
import pytz
import copy
from models.annotation import AnnotationError

class AnnotationCollection(object):

    def __init__(self, data):
        self.creator = data["creator"]
        self.label = data["label"]
        self.type = "AnnotationCollection"
        if 'id' in data:
            self.id = data['id']
        else:
            self.id = uuid.uuid4().urn
        if 'created' in data:
            self.created = data['created']
        else:
            self.created = datetime.datetime.now(pytz.utc).isoformat()
        if 'modified' in data:
            self.modified = data['modified']
        else:
            self.modified = None
        if 'items' in data:
            self.items = data['items']
        else:
            self.items = []
        self.set_permissions(data)

    def set_permissions(self, data):
        self.permissions = data["permissions"] if "permissions" in data else None

    def get_permissions(self):
        return self.permissions

    def update(self, data):
        self.creator = data["creator"]
        self.label = data["label"]
        self.modified = datetime.datetime.now(pytz.utc).isoformat()

    def add_annotation(self, annotation_id):
        if annotation_id in self.items:
            return False
        else:
            self.items.append(annotation_id)
            self.modified = datetime.datetime.now(pytz.utc).isoformat()
            return True

    def has_annotation(self, annotation_id):
        return annotation_id in self.items

    def remove_annotation(self, annotation_id):
        try:
            self.items.remove(annotation_id)
        except ValueError:
            raise AnnotationError(message="Annotation Collection does not contain annotation with id %s" % (annotation_id))
        self.modified = datetime.datetime.now(pytz.utc).isoformat()

    def list_annotations(self):
        return self.items

    def size(self):
        return len(self.items)

    def base_json(self):
        collection = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": self.id,
            "type": self.type,
            "label": self.label,
            "creator": self.creator,
            "created": self.created,
            "total": self.size(),
            "items": self.items
        }
        if self.modified:
            collection["modified"] = self.modified
        return collection

    def to_clean_json(self, params):
        collection = self.base_json()
        if params and "include_permissions" in params and params["include_permissions"]:
            collection["permissions"] = copy.copy(self.permissions)
        return collection

    def to_json(self):
        collection = self.base_json()
        collection["permissions"] = copy.copy(self.permissions)
        return collection

