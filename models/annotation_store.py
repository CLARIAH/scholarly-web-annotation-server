import copy
import json
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection
from models.error import *
import models.queries as query_helper
import models.permissions as permissions
from elasticsearch import Elasticsearch
#from elasticsearch.exceptions import NotFoundError

class AnnotationStore(object):

    def __init__(self, annotations=[]):
        for annotation in annotations:
            self.add_annotation(annotation)

    def configure_index(self, configuration):
        self.es_config = configuration
        self.es_index = configuration['annotation_index']
        self.es = Elasticsearch([{"host": self.es_config['host'], "port": self.es_config['port']}])
        if not self.es.indices.exists(index=self.es_index):
            self.es.indices.create(index=self.es_index)
        self.needs_refresh = False

    def index_needs_refresh(self):
        return self.needs_refresh

    def index_refresh(self):
        self.es.indices.refresh(index=self.es_index)
        self.needs_refresh = False

    def set_index_needs_refresh(self):
        self.needs_refresh = True

    def check_index_is_fresh(self):
        # check index is up to date, refresh if needed
        if self.index_needs_refresh():
            self.index_refresh()

    def add_annotation_es(self, annotation, params):
        # check if annotation is valid, add id and timestamp
        anno = Annotation(annotation)
        # if annotation already has ID, check if it already exists in the index
        if "id" in annotation:
            self.should_not_exist(annotation['id'], annotation['type'])
        # add permissions for access (see) and update (edit)
        permissions.add_permissions(anno, params)
        # create target_list for easy target-based retrieval
        self.add_target_list(anno)
        # index annotation
        self.add_to_index(anno.to_json(), annotation["type"])
        # set index needs refresh before next GET
        self.set_index_needs_refresh()
        # exclude target_list and permissions when returning annotation
        return anno.to_clean_json(params)

    def create_collection_es(self, collection_data, params):
        # check if collection is valid, add id and timestamp
        collection = AnnotationCollection(collection_data)
        # if collection already has ID, check if it already exists in the index
        if "id" in collection_data:
            self.should_not_exist(collection_data['id'], collection_data['type'])
        # add permissions for access (see) and update (edit)
        permissions.add_permissions(collection, params)
        # index collection
        self.add_to_index(collection.to_json(), collection.type)
        # set index needs refresh before next GET
        self.set_index_needs_refresh()
        # return collection to caller
        return collection.to_clean_json(params)

    def add_annotation_to_collection_es(self, annotation_id, collection_id, params):
        # check that user is allowed to edit collection
        collection = self.get_from_index_if_allowed(collection_id,
                                                    username=params["username"],
                                                    action="edit",
                                                    annotation_type="AnnotationCollection")
        # check if collection contains annotation
        if collection.has_annotation(annotation_id):
            raise AnnotationError(message="Collection already contains this annotation")
        # check that user is allowed to see annotation
        self.get_from_index_if_allowed(annotation_id,
                                                    username=params["username"],
                                                    action="see",
                                                    annotation_type="Annotation")
        # add annotation
        collection.add_annotation(annotation_id)
        # add permissions for access (see) and update (edit)
        permissions.add_permissions(collection, params)
        self.update_in_index(collection.to_json(), "AnnotationCollection")
        # set index needs refresh before next GET
        self.set_index_needs_refresh()
        # return collection metadata
        return collection.to_clean_json(params)

    def get_annotation_es(self, annotation_id, params):
        if "action" not in params:
            params["action"] = "see"
        if "username" not in params:
            params["username"] = None
        # get annotation from index
        annotation = self.get_from_index_if_allowed(annotation_id,
                                                    username=params["username"],
                                                    action=params["action"],
                                                    annotation_type="Annotation")
        return annotation.to_clean_json(params)

    def get_annotations_es(self, params):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        response = self.get_from_index_by_filters(params, annotation_type="Annotation")
        annotations = [Annotation(hit["_source"]) for hit in response["hits"]["hits"]]
        return {
            "total": response["hits"]["total"],
            "annotations": [annotation.to_clean_json(params) for annotation in annotations]
        }

    def get_annotations_by_id_es(self, annotation_ids, params):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        response = self.es.mget(index=self.es_index, doc_type="Annotation", body={"ids": annotation_ids})
        return [hit["_source"] for hit in response["hits"]["hits"]]

    def get_collection_es(self, collection_id, params):
        if "action" not in params:
            params["action"] = "see"
        if "username" not in params:
            params["username"] = None
        # get collection from index
        collection = self.get_from_index_if_allowed(collection_id,
                                                    username=params["username"],
                                                    action=params["action"],
                                                    annotation_type="AnnotationCollection")
        return collection.to_clean_json(params)

    def get_collections_es(self, params):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        response = self.get_from_index_by_filters(params, annotation_type="AnnotationCollection")
        collections = [AnnotationCollection(hit["_source"]) for hit in response["hits"]["hits"]]
        return {
            "total": response["hits"]["total"],
            "collections": [collection.to_clean_json(params) for collection in collections]
        }

    def update_annotation_es(self, updated_annotation_json, params):
        if "action" not in params:
            params["action"] = "edit"
        annotation = self.get_from_index_if_allowed(updated_annotation_json["id"],
                                                    username=params["username"],
                                                    action=params["action"],
                                                    annotation_type="Annotation")
        # get copy of original target list
        old_target_list = copy.copy(annotation.to_json()["target_list"])
        # update annotation with new data
        annotation.update(updated_annotation_json)
        # update permissions if given
        permissions.add_permissions(annotation, params)
        # update target_list
        self.add_target_list(annotation)
        # index updated annotation
        self.update_in_index(annotation.to_json(), annotation.type)
        # if target list has changed, annotations targeting this annotation should also be updated
        if self.target_list_changed(annotation.to_json()["target_list"], old_target_list):
            # updates annotations that target this updated annotation
            self.update_chained_annotations(annotation.id)
        # set index needs refresh before next GET
        self.set_index_needs_refresh()
        # return annotation to caller
        return annotation.to_clean_json(params)

    def update_chained_annotations(self, annotation_id):
        # first refresh the index
        self.es.indices.refresh(index=self.es_index)
        chain_annotations = self.get_from_index_by_target({"id": annotation_id})
        for chain_annotation in chain_annotations:
            if chain_annotation["id"] == annotation_id:
                raise AnnotationError(message="Annotation cannot target itself")
            chain_annotation["target_list"] = self.get_target_list(Annotation(chain_annotation))
            # don't use permission parameters for chained annotations
            self.update_annotation_es(chain_annotation, params={"username": None, "action": "traverse"})

    def update_collection_es(self, collection_json):
        self.should_exist(collection_json["id"], "AnnotationCollection")
        collection = AnnotationCollection(self.get_from_index_by_id(collection_json["id"], "AnnotationCollection"))
        collection.update(collection_json)
        self.update_in_index(collection.to_json(), "AnnotationCollection")
        # set index needs refresh before next GET
        self.set_index_needs_refresh()
        return collection.to_json()

    def remove_annotation_es(self, annotation_id, params):
        if params and "action" not in params:
            params["action"] = "edit"
        # remove annotation from index
        self.remove_from_index_if_allowed(annotation_id, params, annotation_type="Annotation")
        # replace with deleted annotation with same id
        deleted_annotation = {
            "id": annotation_id,
            "type": "Annotation",
            "status": "deleted"
        }
        self.add_to_index(deleted_annotation, "Annotation")
        # updates annotations that target this deleted annotation
        self.update_chained_annotations(annotation_id)
        return deleted_annotation

    def remove_annotation_from_collection_es(self, annotation_id, collection_id, params):
        # check that user is allowed to edit collection
        collection = self.get_from_index_if_allowed(collection_id,
                                                    username=params["username"],
                                                    action="edit",
                                                    annotation_type="AnnotationCollection")
        # check if collection contains annotation
        if not collection.has_annotation(annotation_id):
            raise AnnotationError(message="Collection doesn't contain this annotation")
        # check that user is allowed to see annotation
        self.get_from_index_if_allowed(annotation_id,
                                                    username=params["username"],
                                                    action="see",
                                                    annotation_type="Annotation")
        # remove annotation
        collection.remove_annotation(annotation_id)
        self.update_in_index(collection.to_json(), "AnnotationCollection")
        # return collection metadata
        return collection.to_json()

    def remove_collection_es(self, collection_id, params):
        # check that user is allowed to edit collection
        self.get_from_index_if_allowed(collection_id,
                                        username=params["username"],
                                        action="edit",
                                        annotation_type="AnnotationCollection")
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
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

    ####################
    # Helper functions #
    ####################

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
                target_annotation = self.get_annotation_es(target['id'], params={"username": None, "action": "traverse"})
                deeper_targets += self.get_target_list(Annotation(target_annotation))
        target_ids = [target["id"] for target in target_list]
        for target in deeper_targets:
            if target not in target_ids:
                target_list += [target]
                target_ids += [target["id"]]
        return target_list

    def add_target_list(self, annotation):
        annotation.target_list = self.get_target_list(annotation)

    def is_annotation(self, target):
        if "type" in target:
            if type(target["type"]) == str and target["type"] == "Annotation":
                return True
            if type(target["type"]) == list and "Annotation" in target["type"]:
                return True
        return False

    ###################
    # ES interactions #
    ###################

    def add_to_index(self, annotation, annotation_type):
        self.should_have_target_list(annotation)
        self.should_have_permissions(annotation)
        self.should_not_exist(annotation['id'], annotation_type)
        return self.es.index(index=self.es_index, doc_type=annotation_type, id=annotation['id'], body=annotation)

    def add_bulk_to_index(self, annotations, annotation_type):
        raise ValueError("Function not yet implemented")

    def get_from_index_if_allowed(self, annotation_id, username, action, annotation_type="_all"):
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        # check that annotation exists (and is not deleted)
        self.should_exist(annotation_id, annotation_type)
        # get original annotation json
        annotation_json = self.get_from_index_by_id(annotation_id, annotation_type)
        annotation = Annotation(annotation_json) if annotation_json["type"] == "Annotation" else AnnotationCollection(annotation_json)
        # check if user has appropriate permissions
        if not permissions.is_allowed_action(username, action, annotation):
            raise PermissionError(message="Unauthorized access - no permission to {a} annotation".format(a=action))
        return annotation

    def get_from_index_by_id(self, annotation_id, annotation_type="_all"):
        self.should_exist(annotation_id, annotation_type)
        return self.es.get(index=self.es_index, doc_type=annotation_type, id=annotation_id)['_source']

    def get_from_index_by_filters(self, params, annotation_type="_all"):
        filter_queries = query_helper.make_param_filter_queries(params)
        filter_queries += [query_helper.make_permission_see_query(params)]
        query = {
            "from": params["page"] * self.es_config["page_size"],
            "size": self.es_config["page_size"],
            "query": query_helper.bool_must(filter_queries)
        }
        return self.es.search(index=self.es_index, doc_type=annotation_type, body=query)

    def get_from_index_by_target(self, target):
        target_list_query = query_helper.make_target_list_query(target)
        query = {"query": query_helper.bool_must([target_list_query])}
        response = self.es.search(index=self.es_index, doc_type="Annotation", body=query)
        return [hit["_source"] for hit in response['hits']['hits']]

    def get_from_index_by_target_list(self, target, params):
        target_list_query = query_helper.make_target_list_query(target)
        permission_query = query_helper.make_permission_see_query(params)
        query = {"query": query_helper.bool_must([target_list_query, permission_query])}
        response = self.es.search(index=self.es_index, doc_type="Annotation", body=query)
        return [hit["_source"] for hit in response['hits']['hits']]

    def update_in_index(self, annotation, annotation_type):
        self.should_have_target_list(annotation)
        self.should_have_permissions(annotation)
        self.should_exist(annotation['id'], annotation_type)
        return self.es.index(index=self.es_index, doc_type=annotation_type, id=annotation['id'], body=annotation)

    def should_have_target_list(self, annotation):
        if "status" in annotation and annotation["status"] == "deleted":
            return False
        if annotation["type"] == "AnnotationCollection":
            return False
        if "target_list" not in annotation or not annotation["target_list"]:
            raise AnnotationError(message="{t} should have target list".format(t=annotation["type"]))
        return True

    def should_have_permissions(self, annotation):
        if "status" in annotation and annotation["status"] == "deleted":
            return False
        if "permissions" not in annotation or not annotation["permissions"]:
            raise PermissionError(message="{t} should have permission information".format(t=annotation["type"]))
        return True

    def remove_from_index(self, annotation_id, annotation_type):
        self.should_exist(annotation_id, annotation_type)
        return self.es.delete(index=self.es_index, doc_type=annotation_type, id=annotation_id)

    def remove_from_index_if_allowed(self, annotation_id, params, annotation_type="_all"):
        if "username" not in params:
            params["username"] = None
        # check index is up to date, refresh if needed
        self.check_index_is_fresh()
        # check that annotation exists (and is not deleted)
        self.should_exist(annotation_id, annotation_type)
        # get original annotation json
        annotation_json = self.get_from_index_by_id(annotation_id, annotation_type)
        # check if user has appropriate permissions
        if not permissions.is_allowed_action(params["username"], "edit", Annotation(annotation_json)):
            raise PermissionError(message="Unauthorized access - no permission to {a} annotation".format(a=params["action"]))
        return self.remove_from_index(annotation_id, "Annotation")

    def is_deleted(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_index, doc_type=annotation_type, id=annotation_id):
            res = self.es.get(index=self.es_index, doc_type=annotation_type, id=annotation_id)
            if "status" in res["_source"] and res["_source"]["status"] == "deleted":
                return True
        return False

    def should_exist(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_index, doc_type=annotation_type, id=annotation_id):
            if not self.is_deleted(annotation_id, annotation_type):
                return True
        raise AnnotationError(message="Annotation with id %s does not exist" % (annotation_id), status_code=404)

    def should_not_exist(self, annotation_id, annotation_type="_all"):
        if self.es.exists(index=self.es_index, doc_type=annotation_type, id=annotation_id):
            raise AnnotationError(message="Annotation with id %s already exists" % (annotation_id))
        else:
            return True

    def get_objects_from_hits(self, hits):
        objects = []
        for hit in hits:
            if hit["_source"]["type"] == "Annotation":
                objects += [Annotation(hit["_source"])]
            elif hit["_source"]["type"] == "AnnotationCollection":
                objects += [AnnotationCollection(hit["_source"])]



    def list_annotation_ids(self):
        return list(self.annotation_index.keys())

    def list_annotations(self, ids=None):
        if not ids:
            ids = self.list_annotation_ids()
        return [annotation for id, annotation in self.annotation_index.items() if id in ids]

    def list_annotations_as_json(self, ids=None):
        if not ids:
            ids = self.list_annotation_ids()
        return [annotation.to_json() for id, annotation in self.annotation_index.items() if id in ids]

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




