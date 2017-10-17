import unittest
import copy, string, random, time
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationError
from models.annotation_store import AnnotationStore

class TestAnnotationStore(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()
        self.temp_index_name = "test-index-%s" % (''.join(random.choices(string.ascii_lowercase + string.digits, k=16)))
        self.config = {
            "host": "localhost",
            "port": 9200,
            "index": self.temp_index_name,
            "page_size": 1000
        }
        self.store.configure_index(self.config)
        self.example_annotation = copy.copy(examples["vincent"])

    def tearDown(self):
        # make sure to remove temp index
        self.store.es.indices.delete(self.temp_index_name)

    def test_temp_index_is_created(self):
        exists = False
        for index in self.store.es.indices.get('*'):
            if index == self.temp_index_name:
                exists = True
        self.assertTrue(exists)

    def test_store_can_add_annotation_to_index(self):
        anno = Annotation(self.example_annotation)
        response = self.store.add_to_index(anno.data, anno.data['type'])
        self.assertEqual(response['result'], "created")
        res = self.store.es.get(index=self.config['index'], doc_type=anno.data['type'], id=anno.data['id'])
        self.assertEqual(res['_source']['id'], anno.data['id'])

    def test_store_cannot_add_annotation_with_existing_id_to_index(self):
        anno = Annotation(self.example_annotation)
        response = self.store.add_to_index(anno.data, anno.data['type'])
        self.assertEqual(response['result'], "created")
        error = None
        try:
            self.store.add_to_index(anno.data, anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s already exists" % anno.data['id'])

    def test_store_raises_error_getting_unknown_annotation_from_index(self):
        error = None
        anno = Annotation(self.example_annotation)
        try:
            self.store.get_from_index(anno.data['id'], anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data['id'])

    def test_store_can_get_annotation_from_index(self):
        anno = Annotation(self.example_annotation)
        response = self.store.add_to_index(anno.data, anno.data['type'])
        self.assertEqual(response['result'], "created")
        response = self.store.get_from_index(anno.data['id'], anno.data['type'])
        self.assertEqual(response['id'], anno.data['id'])
        self.assertEqual(response['type'], anno.data['type'])

    def test_store_can_get_annotations_from_index_by_target(self):
        anno = Annotation(self.example_annotation)
        anno.data["target_list"] = self.store.get_target_list(anno)
        self.store.add_to_index(anno.data, anno.data['type'])
        time.sleep(1) # wait for indexing of target_list field to finish
        response = self.store.get_from_index_by_target({"id": anno.data["target"][0]["id"]})
        self.assertEqual(len(response), 1)
        self.assertEqual(response[0]['id'], anno.data['id'])
        self.assertEqual(response[0]['type'], anno.data['type'])

    def test_store_raises_error_updating_unknown_annotation_from_index(self):
        error = None
        anno = Annotation(self.example_annotation)
        try:
            self.store.update_in_index(anno.data, anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data['id'])

    def test_store_can_update_annotation_in_index(self):
        anno = Annotation(self.example_annotation)
        self.store.add_to_index(anno.data, anno.data['type'])
        response = self.store.update_in_index(anno.data, anno.data['type'])
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
        response = self.store.add_to_index(anno.data, anno.data['type'])
        self.assertEqual(response['result'], "created")
        response = self.store.remove_from_index(anno.data['id'], anno.data['type'])
        self.assertEqual(response['result'], "deleted")
        try:
            self.store.get_from_index(anno.data['id'], anno.data['type'])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Annotation with id %s does not exist" % anno.data['id'])

    def test_store_can_add_annotation(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        self.assertTrue("id" in stored_annotation)
        res = self.store.es.get(index=self.config['index'], doc_type=stored_annotation['type'], id=stored_annotation['id'])
        self.assertEqual(res['_source']['id'], stored_annotation['id'])

    def test_store_can_get_annotation(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"])
        self.assertEqual(retrieved_annotation['id'], stored_annotation['id'])

    def test_store_can_get_annotation_by_target_id(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        retrieved_annotations = self.store.get_annotations_by_target_es({"id": stored_annotation["target"][0]["id"]})
        self.assertEqual(len(retrieved_annotations), 1)
        self.assertEqual(retrieved_annotations[0]["id"], stored_annotation["id"])
        retrieved_annotations = self.store.get_annotations_by_target_es({"type": stored_annotation["target"][0]["type"]})
        self.assertEqual(retrieved_annotations[0]["id"], stored_annotation["id"])

    def test_store_can_update_annotation(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        retrieved_annotation = self.store.get_annotation_es(stored_annotation["id"])
        retrieved_annotation["creator"] = "someone else"
        updated_annotation = self.store.update_annotation_es(retrieved_annotation)
        self.assertEqual(updated_annotation["creator"], retrieved_annotation["creator"])

    def test_store_propagates_update_along_annotation_chain(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        self.store.get_annotation_es(stored_annotation["id"])
        chain_annotation = copy.copy(examples["vincent"])
        chain_annotation["target"] = {
            "id": stored_annotation["id"],
            "type": "Annotation",
            "selector": None
        }
        stored_chain_annotation = self.store.add_annotation_es(chain_annotation)
        self.store.get_annotation_es(stored_chain_annotation["id"])
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        new_target = "urn:vangogh:differentletter"
        stored_annotation["target"][0]["id"] = new_target
        self.store.update_annotation_es(stored_annotation)
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        retrieved_annotations = self.store.get_from_index_by_target({"id": new_target})
        self.assertTrue(stored_chain_annotation["id"] in [anno["id"] for anno in retrieved_annotations])

    def test_store_can_remove_annotation(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        self.store.remove_annotation_es(stored_annotation["id"])
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        error = None
        try:
            self.store.get_annotation_es(stored_annotation["id"])
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_store_propagates_delete_along_annotation_chain(self):
        stored_annotation = self.store.add_annotation_es(self.example_annotation)
        self.store.get_annotation_es(stored_annotation["id"])
        chain_annotation = copy.copy(examples["vincent"])
        chain_annotation["target"] = {
            "id": stored_annotation["id"],
            "type": "Annotation",
            "selector": None
        }
        stored_chain_annotation = self.store.add_annotation_es(chain_annotation)
        self.store.get_annotation_es(stored_chain_annotation["id"])
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        self.store.remove_annotation_es(stored_annotation["id"])
        # refresh index to make document available for search
        self.store.es.indices.refresh(index=self.config["index"])
        retrieved_annotations = self.store.get_from_index_by_target({"id": stored_annotation["target"][0]["id"]})
        self.assertEqual(len(retrieved_annotations), 0)

    def test_store_can_add_annotation_collection(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data)
        self.assertEqual(collection["label"], collection_data["label"])
        self.assertNotEqual(collection["id"], None)

    def test_store_can_add_annotation_to_collection(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]))
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data)
        self.store.add_annotation_to_collection_es(annotation['id'], collection["id"])
        collection = self.store.get_collection_es(collection["id"])
        self.assertEqual(collection["total"], 1)
        self.assertEqual(collection["items"][0], annotation["id"])

    def test_store_can_remove_annotation_from_collection(self):
        annotation = self.store.add_annotation_es(copy.copy(examples["vincent"]))
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data)
        self.store.add_annotation_to_collection_es(annotation['id'], collection["id"])
        self.store.remove_annotation_from_collection_es(annotation["id"], collection["id"])
        collection = self.store.get_collection_es(collection["id"])
        self.assertEqual(collection["total"], 0)

    def test_store_can_remove_annotation_collection(self):
        collection_data = example_collections["empty_collection"]
        collection = self.store.create_collection_es(collection_data)
        self.store.remove_collection_es(collection["id"])
        error = None
        try:
            self.store.get_collection_es(collection["id"])
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)


if __name__ == "__main__":
    unittest.main()


