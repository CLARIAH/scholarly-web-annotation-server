import unittest
import copy, time
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationError
from models.annotation_store import AnnotationStore
from models.permissions import add_permissions
from models.error import *

class TestAnnotationStore(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()
        self.config = {
            "host": "localhost",
            "port": 9200,
            "annotation_index": "unittest-test-index",
            "page_size": 1000
        }
        self.store.configure_index(self.config)
        self.example_annotation = copy.copy(examples["vincent"])
        self.params = {
            "page": 0,
            "access_status": "private",
            "username": "user1"
        }
        self.private_params = {
            "page": 0,
            "access_status": "private",
            "username": "user1"
        }
        self.private_other_params = {
            "page": 0,
            "access_status": "private",
            "username": "user2"
        }
        self.public_params = {
            "page": 0,
            "access_status": "public",
            "username": "user1"
        }
        self.public_other_params = {
            "page": 0,
            "access_status": "public",
            "username": "user2"
        }
        self.shared_params = {
            "page": 0,
            "access_status": "shared",
            "username": "user1",
            "can_see": ["user2", "user3"],
            "can_edit": ["user2"]
        }
        self.shared_other_params = {
            "page": 0,
            "access_status": "shared",
            "username": "user2",
            "can_see": ["user3"],
            "can_edit": ["user3"]
        }
        self.anon_params = {
            "page": 0,
            "access_status": "public",
            "username": None
        }

    def tearDown(self):
        # make sure to remove temp index
        self.store.es.indices.delete(self.config["annotation_index"])

    def test_temp_index_is_created(self):
        exists = False
        for index in self.store.es.indices.get('*'):
            if index == self.config["annotation_index"]:
                exists = True
        self.assertTrue(exists)

    def test_store_raises_error_updating_annotation_from_index_without_target_list(self):
        error = None
        anno = Annotation(self.example_annotation)
        try:
            self.store.update_in_index(anno.to_json(), anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation should have target list")

    def test_store_raises_error_updating_annotation_from_index_without_permissions(self):
        error = None
        annotation = Annotation(self.example_annotation)
        self.store.add_target_list(annotation)
        try:
            self.store.update_in_index(annotation.to_json(), annotation.type)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation should have permission information")

    def test_store_can_add_annotation_to_index(self):
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        response = self.store.add_to_index(anno.to_json(), anno.data["type"])
        self.assertEqual(response["result"], "created")
        res = self.store.es.get(index=self.config["annotation_index"], doc_type=anno.data["type"], id=anno.data["id"])
        self.assertEqual(res["_source"]["id"], anno.data["id"])

    def test_store_cannot_add_annotation_with_existing_id_to_index(self):
        annotation = Annotation(self.example_annotation)
        self.store.add_target_list(annotation)
        add_permissions(annotation, self.private_params)
        response = self.store.add_to_index(annotation.to_json(), annotation.type)
        self.assertEqual(response["result"], "created")
        error = None
        try:
            self.store.add_to_index(annotation.to_json(), annotation.type)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s already exists" % annotation.id)

    def test_store_raises_error_getting_unknown_annotation_from_index(self):
        error = None
        annotation = Annotation(self.example_annotation)
        try:
            self.store.get_from_index_by_id(annotation.id, annotation.type)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % annotation.id)

    def test_store_can_get_annotation_from_index(self):
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        response = self.store.add_to_index(anno.to_json(), anno.data['type'])
        self.assertEqual(response['result'], "created")
        response = self.store.get_from_index_by_id(anno.data['id'], anno.data['type'])
        self.assertEqual(response['id'], anno.data['id'])
        self.assertEqual(response['type'], anno.data['type'])

    def test_store_can_get_annotations_from_index_by_target(self):
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        anno.data["target_list"] = self.store.get_target_list(anno)
        self.store.add_to_index(anno.to_json(), anno.data['type'])
        time.sleep(1) # wait for indexing of target_list field to finish
        response = self.store.get_from_index_by_target({"id": anno.data["target"][0]["id"]})
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], anno.data['id'])
        self.assertEqual(response[0]['type'], anno.data['type'])

    def test_store_raises_error_updating_unknown_annotation_from_index(self):
        error = None
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        try:
            self.store.update_in_index(anno.to_json(), anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data['id'])

    def test_store_can_update_annotation_in_index(self):
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        self.store.add_to_index(anno.to_json(), anno.data['type'])
        response = self.store.update_in_index(anno.to_json(), anno.data['type'])
        self.assertEqual(response['result'], "updated")

    def test_store_raises_error_removing_unknown_annotation_from_index(self):
        anno = Annotation(self.example_annotation)
        try:
            self.store.remove_from_index(anno.data['id'], anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data['id'])

    def test_store_can_remove_annotation_from_index(self):
        anno = Annotation(self.example_annotation)
        self.store.add_target_list(anno)
        add_permissions(anno, self.private_params)
        response = self.store.add_to_index(anno.to_json(), anno.data["type"])
        self.assertEqual(response["result"], "created")
        response = self.store.remove_from_index(anno.data["id"], anno.data["type"])
        self.assertEqual(response["result"], "deleted")
        error = None
        try:
            self.store.get_from_index_by_id(anno.data["id"], anno.data["type"])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data["id"])

    def test_store_cannot_add_annotation_as_anonymous_user(self):
        error = None
        try:
            self.store.add_annotation_es(self.example_annotation, self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Cannot add annotation as unknown user")

    def test_store_can_add_annotation_as_known_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        self.assertTrue("id" in stored_annotation)
        res = self.store.es.get(index=self.config["annotation_index"], doc_type=stored_annotation["type"], id=stored_annotation["id"])
        anno = res["_source"]
        self.assertEqual(anno["id"], stored_annotation["id"])
        self.assertEqual(anno["permissions"]["access_status"], self.params["access_status"])
        self.assertEqual(anno["permissions"]["owner"], self.params["username"])

    def test_store_cannot_get_private_annotation_as_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_get_private_annotation_as_non_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.private_other_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_get_private_annotation_as_owner(self):
        annotation = Annotation(self.example_annotation)
        self.store.add_target_list(annotation)
        add_permissions(annotation, self.private_params)
        self.store.add_to_index(annotation.to_json(), annotation.data["type"])
        retrieved_annotation = self.store.get_annotation_es(annotation.id, self.private_params)
        self.assertEqual(retrieved_annotation["id"], annotation.id)

    def test_store_get_private_annotation_as_owner_has_no_permissions_included(self):
        annotation = Annotation(self.example_annotation)
        self.store.add_target_list(annotation)
        add_permissions(annotation, self.private_params)
        self.store.add_to_index(annotation.to_json(), annotation.data["type"])
        retrieved_annotation = self.store.get_annotation_es(annotation.id, self.private_params)
        self.assertEqual(retrieved_annotation["id"], annotation.id)
        self.assertEqual("permissions" in retrieved_annotation, False)

    def test_store_can_get_private_annotation_with_permissions_as_owner(self):
        annotation = Annotation(self.example_annotation)
        self.store.add_target_list(annotation)
        add_permissions(annotation, self.private_params)
        self.store.add_to_index(annotation.to_json(), annotation.data["type"])
        params = copy.copy(self.private_params)
        params["include_permissions"] = True
        retrieved_annotation = self.store.get_annotation_es(annotation.id, params)
        self.assertEqual(retrieved_annotation["id"], annotation.id)
        self.assertEqual(retrieved_annotation["permissions"]["owner"], params["username"])

    def test_store_cannot_get_private_annotation_by_target_id_as_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.anon_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 0)

    def test_store_cannot_get_shared_annotation_by_target_id_as_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.anon_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 0)

    def test_store_can_get_public_annotation_by_target_id_as_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.anon_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)

    def test_store_cannot_get_private_annotation_by_target_id_as_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.private_other_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 0)

    def test_store_can_get_shared_annotation_by_target_id_as_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.shared_other_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)

    def test_store_can_get_public_annotation_by_target_id_as_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.public_other_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)

    def test_store_can_get_private_annotation_by_target_id_as_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.private_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)
        self.assertEqual(retrieved_annotations["annotations"][0]["id"], stored_annotation["id"])

    def test_store_can_get_shared_annotation_by_target_id_as_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.shared_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)
        self.assertEqual(retrieved_annotations["annotations"][0]["id"], stored_annotation["id"])

    def test_store_can_get_public_annotation_by_target_id_as_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.public_params)
        params["filter"] = {"target_id": stored_annotation["target"][0]["id"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)
        self.assertEqual(retrieved_annotations["annotations"][0]["id"], stored_annotation["id"])

    def test_store_can_get_private_annotation_by_target_type_as_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        params = copy.copy(self.private_params)
        params["filter"] = {"target_type": stored_annotation["target"][0]["type"]}
        retrieved_annotations = self.store.get_annotations_es(params)
        self.assertEqual(retrieved_annotations["total"], 1)
        self.assertEqual(retrieved_annotations["annotations"][0]["id"], stored_annotation["id"])
        self.assertEqual(retrieved_annotations["annotations"][0]["type"], stored_annotation["type"])

    def test_store_cannot_update_private_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        retrieved_annotation["creator"] = "someone else"
        error = None
        try:
            self.store.update_annotation_es(retrieved_annotation, self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_update_shared_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.shared_params)
        retrieved_annotation["creator"] = "someone else"
        error = None
        try:
            self.store.update_annotation_es(retrieved_annotation, self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_update_public_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.public_params)
        retrieved_annotation["creator"] = "someone else"
        error = None
        try:
            self.store.update_annotation_es(retrieved_annotation, self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_update_private_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        retrieved_annotation["creator"] = "someone else"
        error = None
        try:
            self.store.update_annotation_es(retrieved_annotation, self.private_other_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_update_shared_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.shared_params)
        retrieved_annotation["creator"] = "someone else"
        updated_annotation = self.store.update_annotation_es(retrieved_annotation, self.shared_other_params)
        self.assertEqual(updated_annotation["creator"], retrieved_annotation["creator"])

    def test_store_cannot_update_public_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.public_params)
        retrieved_annotation["creator"] = "someone else"
        error = None
        try:
            self.store.update_annotation_es(retrieved_annotation, self.public_other_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_update_private_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        retrieved_annotation["creator"] = "someone else"
        updated_annotation = self.store.update_annotation_es(retrieved_annotation, self.private_params)
        self.assertEqual(updated_annotation["creator"], retrieved_annotation["creator"])

    def test_store_can_update_shared_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.shared_params)
        retrieved_annotation["creator"] = "someone else"
        updated_annotation = self.store.update_annotation_es(retrieved_annotation, self.shared_params)
        self.assertEqual(updated_annotation["creator"], retrieved_annotation["creator"])

    def test_store_can_update_public_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"], self.public_params)
        retrieved_annotation["creator"] = "someone else"
        updated_annotation = self.store.update_annotation_es(retrieved_annotation, self.public_params)
        self.assertEqual(updated_annotation["creator"], retrieved_annotation["creator"])

    def test_store_propagates_update_along_annotation_chain(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        chain_annotation = copy.copy(examples["vincent"])
        chain_annotation["target"] = {
            "id": stored_annotation["id"],
            "type": "Annotation",
            "selector": None
        }
        stored_chain_annotation = self.store.add_annotation_es(chain_annotation, self.private_params)
        self.store.get_annotation_es(stored_chain_annotation["id"], self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        new_target = "urn:vangogh:differentletter"
        stored_annotation["target"][0]["id"] = new_target
        self.store.update_annotation_es(stored_annotation, self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        retrieved_annotations = self.store.get_from_index_by_target({"id": new_target})
        self.assertTrue(stored_chain_annotation["id"] in [anno["id"] for anno in retrieved_annotations])

    def test_store_cannot_remove_private_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        error = None
        try:
            self.store.remove_annotation_es(stored_annotation["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_remove_shared_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        error = None
        try:
            self.store.remove_annotation_es(stored_annotation["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_remove_public_annotation_by_anonymous_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        error = None
        try:
            self.store.remove_annotation_es(stored_annotation["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_remove_private_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        error = None
        try:
            self.store.remove_annotation_es(stored_annotation["id"], self.private_other_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_remove_shared_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        self.store.remove_annotation_es(stored_annotation["id"], self.shared_other_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.shared_params)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_remove_public_annotation_by_other_user(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        error = None
        try:
            self.store.remove_annotation_es(stored_annotation["id"], self.public_other_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_remove_private_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        self.store.remove_annotation_es(stored_annotation["id"], self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_remove_shared_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.shared_params)
        self.store.remove_annotation_es(stored_annotation["id"], self.shared_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.shared_params)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_remove_public_annotation_by_owner(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.public_params)
        self.store.remove_annotation_es(stored_annotation["id"], self.public_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"], self.public_params)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_propagates_delete_along_annotation_chain(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation, self.private_params)
        self.store.get_annotation_es(stored_annotation["id"], self.private_params)
        chain_annotation = copy.copy(examples["vincent"])
        chain_annotation["target"] = {
            "id": stored_annotation["id"],
            "type": "Annotation",
            "selector": None
        }
        stored_chain_annotation = self.store.add_annotation_es(chain_annotation, self.private_params)
        self.store.get_annotation_es(stored_chain_annotation["id"], self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        self.store.remove_annotation_es(stored_annotation["id"], self.private_params)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["annotation_index"])
        retrieved_annotations = self.store.get_from_index_by_target({"id": stored_annotation["target"][0]["id"]})
        self.assertEqual(len(retrieved_annotations), 0)

    def test_store_cannot_add_annotation_collection_by_anonymous_user(self):
        collection_data = example_collections["empty_collection"]
        error = None
        try:
            self.store.create_collection_es(collection_data, self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_add_private_annotation_collection_by_owner(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.private_params)
        self.assertEqual(collection["label"], collection_data["label"])
        self.assertNotEqual(collection["id"], None)

    def test_store_can_add_shared_annotation_collection_by_owner(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.shared_params)
        self.assertEqual(collection["label"], collection_data["label"])
        self.assertNotEqual(collection["id"], None)

    def test_store_can_add_public_annotation_collection_by_owner(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.public_params)
        self.assertEqual(collection["label"], collection_data["label"])
        self.assertNotEqual(collection["id"], None)

    def test_store_cannot_add_public_annotation_to_shared_collection_by_anonymous_user(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]), self.public_params)
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.shared_params)
        error = None
        try:
            self.store.add_annotation_to_collection_es(annotation['id'], collection["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_add_accessible_annotation_to_private_collection_by_owner(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]), self.private_params)
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.private_params)
        self.store.add_annotation_to_collection_es(annotation['id'], collection["id"], self.params)
        collection = self.store.get_collection_es(collection["id"], self.private_params)
        self.assertEqual(collection["total"], 1)
        self.assertEqual(collection["items"][0], annotation["id"])

    def test_store_cannot_add_unaccessible_annotation_to_private_collection_by_owner(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]), self.shared_other_params)
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.shared_params)
        error = None
        try:
            self.store.add_annotation_to_collection_es(annotation['id'], collection["id"], self.shared_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_cannot_remove_public_annotation_from_shared_collection_by_anonymous_user(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]), self.public_params)
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.shared_params)
        self.store.add_annotation_to_collection_es(annotation['id'], collection["id"], self.shared_params)
        error = None
        try:
            self.store.remove_annotation_from_collection_es(annotation["id"], collection["id"], self.anon_params)
        except PermissionError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_can_remove_annotation_from_collection_by_owner(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]), self.private_params)
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.private_params)
        self.store.add_annotation_to_collection_es(annotation['id'], collection["id"], self.private_params)
        self.store.remove_annotation_from_collection_es(annotation["id"], collection["id"], self.private_params)
        collection = self.store.get_collection_es(collection["id"], self.private_params)
        self.assertEqual(collection["total"], 0)

    def test_store_can_remove_annotation_collection_by_owner(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data, self.private_params)
        self.store.remove_collection_es(collection["id"], self.private_params)
        error = None
        try:
            self.store.get_collection_es(collection["id"], self.private_params)
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_store_can_get_private_annotations_by_owner(self):
        annotation = copy.copy(self.example_annotation)
        self.store.add_annotation_es(annotation, self.private_params)
        annotation = copy.copy(self.example_annotation)
        self.store.add_annotation_es(annotation, self.private_params)
        params = copy.copy(self.private_params)
        params["page"] = 0
        annotations_data = self.store.get_annotations_es(params)
        self.assertEqual(annotations_data["total"], 2)

    def test_store_can_get_public_annotations_by_anonymous_user(self):
        annotation = copy.copy(self.example_annotation)
        self.store.add_annotation_es(annotation, self.private_params)
        annotation = copy.copy(self.example_annotation)
        self.store.add_annotation_es(annotation, self.public_params)
        params = copy.copy(self.anon_params)
        params["page"] = 0
        annotations_data = self.store.get_annotations_es(params)
        self.assertEqual(annotations_data["total"], 1)
        self.assertEqual(annotations_data["annotations"][0]["id"], annotation["id"])

    def test_store_can_get_private_collections_by_owner(self):
        collection_data = example_collections["empty_collection"]
        self.store.create_collection_es(collection_data, self.private_params)
        self.store.create_collection_es(collection_data, self.private_params)
        params = copy.copy(self.private_params)
        params["page"] = 0
        collections_data = self.store.get_collections_es(params)
        self.assertEqual(collections_data["total"], 2)

    def test_store_can_get_public_collections_by_anonymous_user(self):
        collection_data = example_collections["empty_collection"]
        self.store.create_collection_es(collection_data, self.private_params)
        collection = self.store.create_collection_es(collection_data, self.public_params)
        params = copy.copy(self.anon_params)
        params["page"] = 0
        collections_data = self.store.get_collections_es(params)
        self.assertEqual(collections_data["total"], 1)
        self.assertEqual(collections_data["collections"][0]["id"], collection["id"])


if __name__ == "__main__":
    unittest.main()


