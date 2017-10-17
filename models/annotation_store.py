import copy
import json
from collections import defaultdict
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection
from elasticsearch import Elasticsearch
#from elasticsearch.exceptions import NotFoundError

class AnnotationStore(object):

    def __init__(self, annotations=[]):
        #self.annotation_index = {}
        #self.collection_index = {}
        #self.target_index = defaultdict(list)
        for annotation in annotations:
            self.add_annotation(annotation)

    def configure_index(self, configuration):
        self.es_config = configuration
        self.es_index = configuration['index']
        self.es = Elasticsearch([{"host": self.es_config['host'], "port": self.es_config['port']}])
        if not self.es.indices.exists(index=self.es_index):
            self.es.indices.create(index=self.es_index)

    """
    def create_collection(self, collection_data):
        collection = AnnotationCollection(collection_data)
        self.collection_index[collection.id] = collection
        return collection

    def retrieve_collection(self, collection_id):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        return self.collection_index[collection_id]

    def update_collection(self, collection_id, collection_data):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        self.collection_index[collection_id].update(collection_data)
        return self.collection_index[collection_id]

    def delete_collection(self, collection_id):
        if collection_id not in self.collection_index.keys():
            raise AnnotationError(message="Annotation Store does not contain collection with id %s" % (collection_id))
        collection = self.collection_index[collection_id]
        del self.collection_index[collection_id]
        return collection

    def list_collections(self):
        return [self.collection_index[col_id] for col_id in self.collection_index.keys()]

    def list_collections_as_json(self):
        return [self.collection_index[col_id].to_json() for col_id in self.collection_index.keys()]

    def retrieve_collections(self):
        return [self.collection_index[collection_id] for collection_id in self.collection_index.keys()]

    def add_annotation_to_collection(self, annotation_id, collection_id):
        self.collection_index[collection_id].add_annotation(annotation_id)
        self.annotation_index[annotation_id].add_collection(collection_id)
        return self.collection_index[collection_id]

    def remove_annotation_from_collection(self, annotation_id, collection_id):
        self.collection_index[collection_id].remove_annotation(annotation_id)
        self.annotation_index[annotation_id].remove_collection(collection_id)
        return self.collection_index[collection_id]

    def add_annotation(self, annotation):
        # make a new annotation object
        anno = Annotation(annotation)
        # do nothing if annotation already exists
        if self.has_annotation(anno.id):
            return None
        # add annotation to index
        self.annotation_index[anno.id] = anno
        # add annotation targets to target_index
        self.add_annotation_to_target_index(anno)
        return anno.data

    def add_annotation_to_target_index(self, annotation):
        for target_id in annotation.get_target_ids():
            self.target_index[target_id] += [annotation.id]

    def add_bulk_annotations(self, annotations):
        added = []
        for annotation in annotations:
            added += [self.add_annotation(annotation)]
        return added

    def get_annotation(self, annotation_id):
        try:
            return self.annotation_index[annotation_id].data
        except KeyError:
            raise AnnotationError(message = "There is no annotation with ID %s" % (annotation_id), status_code=404)

    def remove_annotation_from_target_index(self, annotation_id):
        for target_id in self.annotation_index[annotation_id].get_target_ids():
            self.target_index[target_id].remove(annotation_id)
            if self.target_index[target_id] == []:
                del self.target_index[target_id]

    def remove_annotation(self, annotation_id):
        annotation = self.get_annotation(annotation_id) # raises if not exists
        # first remove annotation from target_index
        self.remove_annotation_from_target_index(annotation_id)
        # then remove annotation from collections
        for collection_id in copy.copy(self.annotation_index[annotation_id].in_collection):
            self.remove_annotation_from_collection(annotation_id, collection_id)
        # then remove from index
        del self.annotation_index[annotation_id]
        return annotation

    def update_annotation(self, updated_annotation):
        try:
            annotation = self.annotation_index[updated_annotation['id']]
            self.remove_annotation_from_target_index(annotation.id)
            annotation.update(updated_annotation)
            self.add_annotation_to_target_index(annotation)
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
    """

    def add_annotation_es(self, annotation):
        # check if annotation is valid, add id and timestamp
        anno = Annotation(annotation)
        # if annotation already has ID, check if it already exists in the index
        if "id" in annotation:
            self.should_not_exist(annotation['id'], annotation['type'])
        # create target_list for easy target-based retrieval
        anno.data["target_list"] = self.get_target_list(anno)
        # index annotation
        self.add_to_index(anno.data, annotation["type"])
        # remove target_list for returning annotation
        del anno.data["target_list"]
        # return annotation to caller
        return anno.data

    def create_collection_es(self, collection_data):
        # check if collection is valid, add id and timestamp
        collection = AnnotationCollection(collection_data)
        # if collection already has ID, check if it already exists in the index
        if "id" in collection_data:
            self.should_not_exist(collection_data['id'], collection_data['type'])
        # index collection
        self.add_to_index(collection.to_json(), collection_data["type"])
        # return collection to caller
        return collection.to_json()

    def add_annotation_to_collection_es(self, annotation_id, collection_id):
        # check if annotation exists
        self.should_exist(annotation_id, "Annotation")
        # check if collection exists
        self.should_exist(collection_id, "AnnotationCollection")
        # check if collection contains annotation
        collection = self.get_from_index(collection_id, "AnnotationCollection")
        if annotation_id in collection["items"]:
            raise AnnotationError(message="Collection already contains this annotation")
        # add annotation
        collection["items"] += [annotation_id]
        collection["total"] = len(collection["items"])
        self.update_in_index(collection, "AnnotationCollection")
        # return collection metadata
        return collection

    def get_annotation_es(self, annotation_id):
        # check that annotation exists (and is not deleted)
        self.should_exist(annotation_id, "Annotation")
        # get annotation from index
        annotation = self.get_from_index(annotation_id, "Annotation")
        del annotation["target_list"]
        return annotation

    def get_annotations_es(self, page=0):
        params = {"from": page * self.es_config["page_size"], "size": self.es_config["page_size"]}
        response = self.es.search(index=self.es_config['index'], doc_type="Annotation", body=params)
        return {"total": response["hits"]["total"], "annotations": [hit["_source"] for hit in response["hits"]["hits"]]}

    def get_annotations_by_id_es(self, annotation_ids):
        response = self.es.mget(index=self.es_config['index'], doc_type="Annotation", body={"ids": annotation_ids})
        return [hit["_source"] for hit in response["hits"]["hits"]]

    def get_collection_es(self, collection_id):
        # check that collection exists (and is not deleted)
        self.should_exist(collection_id, "AnnotationCollection")
        # get collection from index
        return self.get_from_index(collection_id, "AnnotationCollection")

    def get_collections_es(self, page=0):
        params = {"from": page * self.es_config["page_size"], "size": self.es_config["page_size"]}
        response = self.es.search(index=self.es_config['index'], doc_type="AnnotationCollection", body=params)
        return {"total": response["hits"]["total"], "collections": [hit["_source"] for hit in response["hits"]["hits"]]}

    def get_annotations_by_target_es(self, annotation_target):
        # get annotation from index
        annotations = self.get_from_index_by_target_list(annotation_target)
        for annotation in annotations:
            del annotation["target_list"]
        # return annotation to caller
        return annotations

    def update_annotation_es(self, updated_annotation_json):
        # get original annotation json
        annotation_json = self.get_from_index(updated_annotation_json["id"], "Annotation")
        # get copy of original target list
        old_target_list = copy.copy(annotation_json["target_list"])
        # turn json into annotation object
        annotation = Annotation(annotation_json)
        # update annotation with new data
        annotation.update(updated_annotation_json)
        # update target_list
        new_target_list = self.get_target_list(annotation)
        annotation.data["target_list"] = new_target_list
        # index updated annotation
        self.update_in_index(annotation.data, annotation.data["type"])
        # if target list has changed, annotations targeting this annotation should also be updated
        if self.target_list_changed(new_target_list, old_target_list):
            # updates annotations that target this updated annotation
            self.update_chained_annotations(annotation.id)
        # remove target_list for returning annotation
        del annotation.data["target_list"]
        # return annotation to caller
        return annotation.data

    def update_chained_annotations(self, annotation_id):
        # first refresh the index
        self.es.indices.refresh(index=self.es_config["index"])
        chain_annotations = self.get_from_index_by_target({"id": annotation_id})
        for chain_annotation in chain_annotations:
            if chain_annotation["id"] == annotation_id:
                raise AnnotationError(message="Annotation cannot target itself")
            chain_annotation["target_list"] = self.get_target_list(Annotation(chain_annotation))
            self.update_annotation_es(chain_annotation)

    def update_collection_es(self, collection_json):
        self.should_exist(collection_json["id"], "AnnotationCollection")
        collection = AnnotationCollection(self.get_from_index(collection_json["id"], "AnnotationCollection"))
        collection.update(collection_json)
        self.update_in_index(collection.to_json(), "AnnotationCollection")
        return collection.to_json()

    def remove_annotation_es(self, annotation_id):
        # check if annotation already exists
        self.should_exist(annotation_id, "Annotation")
        # remove annotation from index
        self.remove_from_index(annotation_id, "Annotation")
        # replace with deleted annotation with same id
        deleted_annotation = {
            "id": annotation_id,
            "type": "Annotation",
            "status": "deleted"
        }
        self.add_to_index(deleted_annotation, "Annotation")
        # updates annotations that target this deletd annotation
        self.update_chained_annotations(annotation_id)
        return deleted_annotation

    def remove_annotation_from_collection_es(self, annotation_id, collection_id):
        # check if annotation exists
        self.should_exist(annotation_id, "Annotation")
        # check if collection exists
        self.should_exist(collection_id, "AnnotationCollection")
        # check if collection contains annotation
        collection = self.get_from_index(collection_id, "AnnotationCollection")
        # remove annotation
        try:
            collection["items"].remove(annotation_id)
        except ValueError:
            raise AnnotationError(message="Collection does not contain this annotation")
        collection["total"] = len(collection["items"])
        self.update_in_index(collection, "AnnotationCollection")
        # return collection metadata
        return collection

    def remove_collection_es(self, collection_id):
        # check if collection already exists
        self.should_exist(collection_id, "AnnotationCollection")
        # remove collection from index
        self.remove_from_index(collection_id, "AnnotationCollection")
        # replace with deleted collection with same id
        deleted_collection = {
            "id": collection_id,
            "type": "AnnotationCollection",
            "status": "deleted"
        }
        self.add_to_index(deleted_collection, "AnnotationCollection")
        return deleted_collection

    def target_list_changed(self, list1, list2):
        ids1 = set([target["id"] for target in list1])
        ids2 = set([target["id"] for target in list2])
        if len(ids1) != len(ids2): return True
        if len(ids1.intersection(ids2)) != len(ids1): return True
        if len(ids1.union(ids2)) != len(ids1): return True
        return False

    def get_target_list(self, annotation):
        target_list = annotation.get_targets_info()
        deeper_targets = []
        for target in target_list:
            if self.is_annotation(target):
                if target["id"] == annotation.id:
                    raise AnnotationError(message="Annotation cannot target itself")
                if self.is_deleted(target["id"]):
                    continue
                target_annotation = self.get_annotation_es(target['id'])
                deeper_targets += self.get_target_list(Annotation(target_annotation))
        target_ids = [target["id"] for target in target_list]
        for target in deeper_targets:
            if target not in target_ids:
                target_list += [target]
                target_ids += [target["id"]]
        return target_list

    def remove_target_list(self, annotation):
        if "target_list" in annotation:
            del annotation["target_list"]
        return annotation

    def is_annotation(self, target):
        if "type" in target:
            if type(target["type"]) == str and target["type"] == "Annotation":
                return True
            if type(target["type"]) == list and "Annotation" in target["type"]:
                return True
        return False

    def add_to_index(self, annotation, annotation_type):
        self.should_not_exist(annotation['id'], annotation_type)
        return self.es.index(index=self.es_config['index'], doc_type=annotation_type, id=annotation['id'], body=annotation)

    def add_bulk_to_index(self, annotations, annotation_type):
        raise ValueError("Function not yet implemented")

    def get_from_index(self, annotation_id, annotation_type):
        self.should_exist(annotation_id, annotation_type)
        return self.es.get(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id)['_source']

    def get_from_index_by_target(self, target):
        response = self.es.search(index=self.es_config['index'], doc_type="Annotation", body=self.make_target_list_query(target))
        return [hit["_source"] for hit in response['hits']['hits']]

    def get_from_index_by_target_list(self, target):
        response = self.es.search(index=self.es_config['index'], doc_type="Annotation", body=self.make_target_list_query(target))
        return [hit["_source"] for hit in response['hits']['hits']]

    def make_target_query(self, target):
        target_field = list(target.keys())[0]
        list_field = "target.%s.keyword" % target_field
        return {"query": {"match": {list_field: target[target_field]}}}

    def make_target_list_query(self, target):
        target_field = list(target.keys())[0]
        list_field = "target_list.%s.keyword" % target_field
        return {"query": {"match": {list_field: target[target_field]}}}

    def update_in_index(self, annotation, annotation_type):
        self.should_exist(annotation['id'], annotation_type)
        return self.es.index(index=self.es_config['index'], doc_type=annotation_type, id=annotation['id'], body=annotation)

    def remove_from_index(self, annotation_id, annotation_type):
        self.should_exist(annotation_id, annotation_type)
        return self.es.delete(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id)

    def is_deleted(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id):
            res = self.es.get(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id)
            if "status" in res["_source"] and res["_source"]["status"] == "deleted":
                return True
        return False

    def should_exist(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id):
            if not self.is_deleted(annotation_id, annotation_type):
                return True
        raise AnnotationError(message="Annotation with id %s does not exist" % (annotation_id))

    def should_not_exist(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_config['index'], doc_type=annotation_type, id=annotation_id):
            raise AnnotationError(message="Annotation with id %s already exists" % (annotation_id))
        else:
            return True



    def list_annotation_ids(self):
        return list(self.annotation_index.keys())

    def list_annotations(self, ids=None):
        if not ids:
            ids = self.list_annotation_ids()
        return [annotation for id, annotation in self.annotation_index.items() if id in ids]

    def list_annotations_as_json(self, ids=None):
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

    def load_annotations_es(self, annotations_file):
        with open(annotations_file, 'r') as fh:
            data = json.loads(fh.read())
        for annotation in data['annotations']:
            try:
                self.add_annotation_es(annotation)
            except AnnotationError:
                pass
        for collection in data['collections']:
            try:
                self.create_collection_es(collection)
            except AnnotationError:
                pass

    def save_annotations(self, annotations_file):
        try:
            data = {
                "annotations": self.list_annotations_as_json(),
                "collections": self.list_collections_as_json()
            }
            with open(annotations_file, 'w') as fh:
                fh.write(json.dumps(data, indent=4, separators=(',', ': ')))
        except FileNotFoundError:
            pass



