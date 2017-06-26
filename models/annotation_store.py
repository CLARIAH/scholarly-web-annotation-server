import copy
import json
from collections import defaultdict
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection

class AnnotationStore(object):

    def __init__(self, annotations=[]):
        self.annotation_index = {}
        self.collection_index = {}
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
        del self.collection_index[collection_id]
        return current_metadata

    def list_collections(self):
        return [self.collection_index[col_id].to_json() for col_id in self.collection_index.keys()]

    def retrieve_collections(self):
        return [self.collection_index[collection_id].to_json() for collection_id in self.collection_index.keys()]

    def add_annotation_to_collection(self, annotation_id, collection_id):
        self.collection_index[collection_id].add_annotation(annotation_id)
        self.annotation_index[annotation_id].add_collection(collection_id)
        return self.collection_index[collection_id].to_json()

    def remove_annotation_from_collection(self, annotation_id, collection_id):
        self.collection_index[collection_id].remove_annotation(annotation_id)
        self.annotation_index[annotation_id].remove_collection(collection_id)
        return self.collection_index[collection_id].to_json()

    def add_annotation(self, annotation):
        # make a new annotation object
        anno = Annotation(annotation)
        # do nothing if annotation already exists
        if self.has_annotation(anno.id):
            return None
        # add annotation to index
        self.annotation_index[anno.id] = anno
        # add annotation targets to target_index
        for target_id in anno.get_target_ids():
            self.target_index[target_id] += [anno.id]
        return anno.data

    def add_bulk_annotations(self, annotations):
        added = []
        for annotation in annotations:
            added += [self.add_annotation(annotation)]
        return added

    def get_annotation(self, annotation_id):
        try:
            return self.annotation_index[annotation_id].data
        except KeyError:
            raise AnnotationError(message = "There is no annotation with ID %s" % (annotation_id))

    def remove_annotation(self, annotation_id):
        annotation = self.get_annotation(annotation_id) # raises if not exists
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

    def update_annotation(self, updated_annotation):
        try:
            annotation = self.annotation_index[updated_annotation['id']]
            annotation.update(updated_annotation)
            return annotation.data
        except KeyError:
            raise AnnotationError(message = "There is no annotation with ID %s" % (updated_annotation['id']))

    def get_annotation_type(self, annotation_id):
        return self.annotation_index[annotation_id].type

    def get_annotations_by_targets(self, target_ids):
        annotations = []
        ids = []
        for target_id in target_ids:
            for annotation in self.get_annotations_by_target(target_id):
                if annotation["id"] not in ids:
                    ids += [annotation["id"]]
                    annotations += [annotation]
        return annotations

    def get_annotations_by_target(self, target_id):
        annotations = []
        ids = []
        for anno_id in self.target_index[target_id]:
            if anno_id not in ids:
                annotations += [self.annotation_index[anno_id].data]
                # add annotations on annotations
                annotations += self.get_annotations_by_target(anno_id)
                ids += [anno_id]
        return annotations

    def has_annotation(self, annotation_id):
        if annotation_id in self.annotation_index:
            return True
        return False

    def list_annotation_ids(self):
        return list(self.annotation_index.keys())

    def list_annotations(self, ids=None):
        if not ids:
            ids = self.list_annotation_ids()
        return [annotation.data for id, annotation in self.annotation_index.items() if id in ids]

    def load_annotations(self, annotations_file):
        try:
            with open(annotations_file, 'r') as fh:
                data = json.loads(fh.read())
            for annotation in data['annotations']:
                self.add_annotation(annotation)
            for collection in data['collections']:
                self.collection_index[collection['id']] = AnnotationCollection(collection)
        except FileNotFoundError:
            pass

    def save_annotations(self, annotations_file):
        try:
            data = {
                "annotations": self.list_annotations(),
                "collections": self.list_collections()
            }
            with open(annotations_file, 'w') as fh:
                fh.write(json.dumps(data, indent=4, separators=(',', ': ')))
        except FileNotFoundError:
            pass



