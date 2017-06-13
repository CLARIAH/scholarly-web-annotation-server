import json
import copy
import pickle
import datetime
import pytz
import uuid
from rfc3987 import parse as parse_IRI
from collections import defaultdict

class WebAnnotationValidator(object):

    def __init__(self):
        self.accepted_types = ["Annotation", "AnnotationCollection", "AnnotationPage"]

    def validate(self, annotation, annotation_type=None):
        self.validate_generic(annotation)
        self.validate_type(annotation, annotation_type)
        return True

    def validate_generic(self, annotation):
        if type(annotation) != dict:
            raise InvalidAnnotation(message='annotation MUST be valid JSON')
        if "@context" not in annotation:
            raise InvalidAnnotation(message='annotation MUST have a @context')
        if annotation["@context"] != "http://www.w3.org/ns/anno.jsonld":
            raise InvalidAnnotation(message='annotation @context MUST include "http://www.w3.org/ns/anno.jsonld"')
        if 'type' not in annotation:
            raise InvalidAnnotation(message='annotation MUST have a type')

    def validate_type(self, annotation, annotation_type):
        anno_type = self.has_valid_type(annotation)
        if annotation_type == None:
            annotation_type = anno_type
        if annotation_type not in self.as_list(annotation['type']):
            raise InvalidAnnotation(message="annotation is not of type %s" % (annotation_type))
        if annotation_type == "Annotation":
            self.validate_annotation(annotation)
        if annotation_type == "AnnotationPage":
            self.validate_annotation_page(annotation)
        if annotation_type == "AnnotationCollection":
            self.validate_annotation_collection(annotation)

    def validate_annotation_collection(self, annotation_collection):
        if "AnnotationCollection" not in self.as_list(annotation_collection['type']):
            raise InvalidAnnotation(message='annotation "type" property MUST include "AnnotationCollection"')
        if "label" not in annotation_collection.keys():
            raise InvalidAnnotation(message='annotation collection MUST have an "label" property with as value a string.')
        if type(annotation_collection["label"]) != str:
            raise InvalidAnnotation(message='annotation collection "label" property MUST be a string.')
        if "total" in annotation_collection.keys():
            if "first" not in annotation_collection.keys():
                raise InvalidAnnotation(message='Non-empty collection MUST have "first" property referencing the first AnnotationPage')
            if "last" not in annotation_collection.keys():
                raise InvalidAnnotation(message='Non-empty collection MUST have "last" property referencing the first AnnotationPage')

    def validate_annotation_page(self, annotation_page):
        if "AnnotationPage" not in self.as_list(annotation_page['type']):
            raise InvalidAnnotation(message='annotation "type" property MUST include "AnnotationPage"')
        if "items" not in annotation_page.keys():
            raise InvalidAnnotation(message='annotation page MUST have an "items" property with as value a list with at least one annotation.')
        if type(annotation_page["items"]) != list or len(annotation_page["items"]) == 0:
            raise InvalidAnnotation(message='annotation page "items" property MUST be a list with at least one annotation.')

    def validate_annotation(self, annotation):
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

    def has_valid_type(self, annotation):
        types = [anno_type for anno_type in self.as_list(annotation["type"]) if anno_type in self.accepted_types]
        if len(types) > 1:
            raise InvalidAnnotation(message="annotation cannot have multiple annotation types")
        if len(types) == 0:
            raise InvalidAnnotation(message='annotation type MUST be one of "Annotation", "AnnotationCollection", "AnnotationPage"')
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
            raise InvalidAnnotation(message="ID of updated annotation does not match ID of existing annotation")

class AnnotationStore(object):

    def __init__(self, annotations=[]):
        self.annotation_index = {}
        self.collection_index = {}
        self.page_index = {}
        self.target_index = defaultdict(list)
        for annotation in annotations:
            self.add_annotation(annotation)

    def configure(self, configuration):
        self.config = configuration

    def create_collection(self, collection_data):
        collection = AnnotationCollection(collection_data)
        self.collection_index[collection.id] = collection
        return collection.to_json()

    def retrieve_collection(self, collection_id):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        return self.collection_index[collection_id].to_json()

    def update_collection(self, collection_id, collection_data):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        self.collection_index[collection_id].update(collection_data)
        return self.collection_index[collection_id].to_json()

    def delete_collection(self, collection_id):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        current_metadata = self.collection_index[collection_id].to_json()
        for page_id in self.collection_index[collection_id].list_pages():
            del self.page_index[page_id]
        del self.collection_index[collection_id]
        return current_metadata

    def retrieve_collections(self):
        return [self.collection_index[collection_id].to_json() for collection_id in self.collection_index.keys()]

    def add_annotation_to_collection(self, annotation_id, collection_id):
        annotation = self.annotation_index[annotation_id]
        new_pages = self.collection_index[collection_id].add_existing(annotation)
        if len(new_pages) > 0:
            for page_id in new_pages:
                self.page_index[page_id] = self.collection_index[collection_id].pages[page_id]
        annotation.in_collection += [collection_id]
        return self.collection_index[collection_id].has_annotation_on_page[annotation.id]

    def remove_annotation_from_collection(self, annotation_id, collection_id):
        removed_page_id = self.collection_index[collection_id].remove(annotation_id)
        if removed_page_id:
            del self.page_index[removed_page_id]
        annotation = self.annotation_index[annotation_id]
        annotation.in_collection.remove(collection_id)

    def retrieve_collection_page(self, page_id):
        return self.page_index[page_id].to_json()

    def add_bulk(self, annotations):
        added = []
        for annotation in annotations:
            added += [self.add_annotation(annotation)]
        return added

    def add_annotation(self, annotation):
        # make a new annotation object
        anno = Annotation(annotation)
        # do nothing if annotation already exists
        if self.exists(anno.id):
            return None
        # add annotation to index
        self.annotation_index[anno.id] = anno
        # add annotation targets to target_index
        for target_id in anno.get_target_ids():
            self.target_index[target_id] += [anno.id]
        return anno.data

    def get(self, annotation_id):
        try:
            return self.annotation_index[annotation_id].data
        except KeyError:
            raise AnnotationDoesNotExistError(annotation_id)

    def remove(self, annotation_id):
        annotation = self.get(annotation_id) # raises if not exists
        # first remove annotation from target_index
        for target_id in self.annotation_index[annotation_id].get_target_ids():
            self.target_index[target_id].remove(annotation_id)
            if self.target_index[target_id] == []:
                del self.target_index[target_id]
        # then remove annotation from collections
        for collection_id in copy.copy(self.annotation_index[annotation_id].in_collection):
            self.remove_annotation_from_collection(annotation_id, collection_id)
        # then remove from index
        del self.annotation_index[annotation_id]
        return annotation

    def update(self, updated_annotation):
        try:
            annotation = self.annotation_index[updated_annotation['id']]
            annotation.update(updated_annotation)
            return annotation.data
        except KeyError:
            raise AnnotationDoesNotExistError(updated_annotation['id'])

    def ids(self):
        return list(self.annotation_index.keys())

    def get_type(self, annotation_id):
        return self.annotation_index[annotation_id].type

    def get_by_targets(self, target_ids):
        annotations = []
        ids = []
        for target_id in target_ids:
            for annotation in self.get_by_target(target_id):
                if annotation["id"] not in ids:
                    ids += [annotation["id"]]
                    annotations += [annotation]
        return annotations

    def get_by_target(self, target_id):
        annotations = []
        ids = []
        for anno_id in self.target_index[target_id]:
            if anno_id not in ids:
                annotations += [self.annotation_index[anno_id].data]
                # add annotations on annotations
                annotations += self.get_by_target(anno_id)
                ids += [anno_id]
        return annotations

    def exists(self, annotation_id):
        if annotation_id in self.annotation_index:
            return True
        return False

    def list(self, ids=None):
        if not ids:
            ids = self.ids()
        return [annotation.data for id, annotation in self.annotation_index.items() if id in ids]

    def get_annotations_by_target(self, target):
        return self.target_index[target]

    def load_annotations(self):
        try:
            with open(self.config['collections_file'], 'r') as fh:
                collections = pickle.load(fh)
        except FileNotFoundError:
            collections = []
        return collections



class AnnotationCollection(object):

    def __init__(self, data):
        self.id = uuid.uuid4().urn
        self.created = datetime.datetime.now(pytz.utc).isoformat()
        self.creator = data["creator"]
        self.label = data["label"]
        self.total = 0
        self.has_annotation_on_page = {}
        self.pages = {}
        self.validator = WebAnnotationValidator()
        self.page_size = data["page_size"] if "page_size" in data else 100
        self.first = None
        self.last = None

    def update(self, data):
        self.creator = data["creator"]
        self.label = data["label"]
        self.page_size = data["page_size"] if "page_size" in data else 100
        self.modified = datetime.datetime.now(pytz.utc).isoformat()


    def add_existing(self, annotations):
        new_pages = []
        if type(annotations) != list:
            annotations = [annotations]
        for annotation in annotations:
            new_page = self.add_annotation(annotation)
            if new_page:
                new_pages += [new_page]
        return new_pages

    def add_annotation(self, annotation):
        new_page_id = None
        if not self.last or self.pages[self.last].is_full():
            new_page_id = self.add_page(self.last)
        self.pages[self.last].add_annotation(annotation)
        self.has_annotation_on_page[annotation.id] = self.pages[self.last].id
        self.total += 1
        return new_page_id

    def add_page(self, prev_id):
        new_page = AnnotationPage(self.id, prev_id=prev_id, start_index=self.total, page_size=self.page_size)
        self.pages[new_page.id] = new_page
        self.last = new_page.id
        if not self.first:
            self.first = new_page.id
        if prev_id in self.pages.keys():
            prev_page = self.pages[prev_id]
            prev_page.set_next(new_page.id)
        return new_page.id

    def get(self, annotation_ids):
        if type(annotation_ids) == str:
            return self.get_annotation(annotation_ids)
        return [self.get_annotation(annotation_id) for annotation_id in annotation_ids]

    def get_annotation(self, annotation_id):
        if annotation_id not in self.has_annotation_on_page.keys():
            raise AnnotationError(message="Annotation Collection does not contain annotation with id %s" % (annotation_id))
        page_id = self.has_annotation_on_page[annotation_id]
        return self.pages[page_id].get(annotation_id).data

    def remove(self, annotation_ids):
        if type(annotation_ids) == str:
            return self.remove_annotation(annotation_ids)
        removed_page_ids = []
        for annotation_id in annotation_ids:
            removed_page_id = self.remove_annotation(annotation_id)
            if removed_page_id and removed_page_id not in removed_page_ids:
                removed_page_ids += [removed_page_id]
        return removed_page_ids

    def remove_annotation(self, annotation_id):
        if annotation_id not in self.has_annotation_on_page.keys():
            raise AnnotationError(message="Annotation Collection does not contain annotation with id %s" % (annotation_id))
        page_id = self.has_annotation_on_page[annotation_id]
        del self.has_annotation_on_page[annotation_id]
        self.total -= 1
        removed_page = None
        if page_id != self.last and self.pages[page_id].annotations == []:
            self.removed_page(page_id) # remove empty page if it's not the last page
            removed_page = page_id
        return removed_page

    def remove_page(self, page_id):
        # page is first and last, prev and next become None
        if page_id == self.first and page_id == self.last:
            self.first = None
            self.last = None
        # page is first, next becomes first
        elif page_id == self.first:
            self.first = self.pages[page_id].next
            self.pages[self.first].prev = None
        # page is last, prev becomes last
        elif page_id == self.last:
            self.last = self.pages[page_id].prev
            self.pages[self.last].next = None
        # page is neither, link prev to next page
        else:
            prev_page = self.pages[page_id].prev
            next_page = self.pages[page_id].next
            self.pages[prev_page].next = next_page
            self.pages[next_page].prev = prev_page
        del self.pages[page_id]

    def list_pages(self):
        return list(self.pages.keys())

    def get_page_json(self, page_id):
        return self.pages[page_id].to_json()

    def to_json(self):
        collection = {
            "id": self.id,
            "label": self.label,
            "creator": self.creator,
            "created": self.created,
            "total": self.total
        }
        try:
            collection["first"] = self.first
        except AttributeError:
            pass
        try:
            collection["last"] = self.last
        except AttributeError:
            pass
        try:
            collection["modified"] = self.modified
        except AttributeError:
            pass
        return collection

class AnnotationPage(object):

    def __init__(self, collection_id, start_index=0, page_size=10, prev_id=None, annotations=[]):
        self.validator = WebAnnotationValidator()
        self.id = uuid.uuid4().urn
        self.part_of = collection_id
        self.page_size = page_size
        self.prev_id = prev_id
        self.set_start_index(start_index)
        self.annotations = []
        self.initialise_annotations(annotations)

    def initialise_annotations(self, annotations):
        if len(annotations) > self.page_size:
            raise AnnotationError(message="AnnotationPage cannot be initialised with more annotations than set by page_size (%s)." % (self.page_size))
        self.add_annotations(annotations)

    def set_start_index(self, start_index):
        if self.prev_id and start_index == 0:
            raise AnnotationError(message="When passing a prev_id, start_index has to be defined and higher than zero.")
        self.start_index = start_index

    def is_full(self):
        return len(self.annotations) == self.page_size

    def set_next(self, page_id):
        self.next_id = page_id

    def add(self, annotation):
        if type(annotation) == list:
            remaining = self.add_annotations(annotation)
            return remaining
        else:
            self.add_annotation(annotation)
            return True

    def add_annotations(self, annotations):
        remaining = []
        for annotation in annotations:
            if self.is_full():
                remaining += [annotation]
            else:
                self.add_annotation(annotation)
        return remaining

    def add_annotation(self, annotation):
        if self.is_full():
            raise AnnotationError(message="Annotation page is full, cannot add annotation")
        self.annotations += [annotation]

    def get(self, annotation_ids):
        if type(annotation_ids) == str:
            return self.get_annotation(annotation_ids)
        return [self.get_annotation(annotation_id) for annotation_id in annotation_ids]

    def get_annotation(self, annotation_id):
        for annotation in self.annotations:
            if annotation.id == annotation_id:
                return annotation
        raise AnnotationError(message="Annotation Page does not contain annotation with id %s" % (annotation_id))

    def remove(self, annotation_ids):
        annotations = self.get(annotation_ids)
        if type(annotations) == list:
            for annotation in annotations:
                self.annotations.remove(annotations)
        else:
            self.annotations.remove(annotations)
        return annotations

    def to_json(self):
        page = {
            "id": self.id,
            "prev": self.prev_id,
            "startIndex": self.start_index,
            "partOf": self.part_of,
            "items": [annotation.data for annotation in self.annotations]
        }
        try:
            page["next"] = self.next_id
        except AttributeError:
            pass
        return page

class InvalidAnnotation(Exception):
    status_code = 400

    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

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

