import unittest
import copy
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationError
from models.annotation_store import AnnotationStore

class TestAnnotationStore(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()

    def test_store_rejects_invalid_annotation(self):
        error = None
        try:
            self.store.add_annotation(examples["no_target"])
        except AnnotationError as e:
            error = e
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_store_accepts_valid_annotation(self):
        error = None
        try:
            self.store.add_annotation(copy.copy(examples["vincent"]))
        except AnnotationError as e:
            error = e
        # error must be defined
        self.assertEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(len(self.store.list_annotation_ids()), 1)

    def test_store_can_get_annotation_by_id(self):
        self.store.add_annotation(copy.copy(examples["vincent"]))
        annotation_id = self.store.list_annotation_ids()[0]
        annotation = self.store.get_annotation(annotation_id)
        self.assertEqual(annotation['id'], annotation_id)

    def test_store_can_get_annotation_by_target_id(self):
        self.store.add_annotation(copy.copy(examples["vincent"]))
        annotation_id = self.store.list_annotation_ids()[0]
        annotation_data = self.store.get_annotation(annotation_id)
        annotation = Annotation(annotation_data)
        target_ids = annotation.get_target_ids()
        for target_id in target_ids:
            target_annotations = self.store.get_annotations_by_target(target_id)
            ids = [target_annotation['id'] for target_annotation in target_annotations]
            self.assertTrue(annotation_data['id'] in ids)

    def test_store_can_update_annotation(self):
        self.store.add_annotation(copy.copy(examples["vincent"]))
        annotation_id = self.store.list_annotation_ids()[0]
        annotation = self.store.get_annotation(annotation_id)
        annotation['motivation'] = "linking"
        updated_annotation = self.store.update_annotation(annotation)
        self.assertEqual(updated_annotation['id'], annotation_id)
        self.assertTrue('modified' in updated_annotation)

    def test_store_can_remove_annotation(self):
        self.store.add_annotation(copy.copy(examples["vincent"]))
        annotation_id = self.store.list_annotation_ids()[0]
        self.assertEqual(len(self.store.list_annotation_ids()), 1)
        annotation = self.store.remove_annotation(annotation_id)
        self.assertEqual(len(self.store.list_annotation_ids()), 0)
        self.assertEqual(annotation["motivation"], examples["vincent"]["motivation"])
        self.assertEqual(len(self.store.target_index.keys()), 0)

    def test_store_can_add_annotation_collection(self):
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.assertEqual(collection_json["label"], collection_data["label"])
        self.assertNotEqual(collection_json["id"], None)

    def test_store_can_add_annotation_to_collection(self):
        annotation = self.store.add_annotation(copy.copy(examples["vincent"]))
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.add_annotation_to_collection(annotation['id'], collection_json["id"])
        collection_json = self.store.retrieve_collection(collection_json["id"])
        self.assertEqual(collection_json["total"], 1)
        self.assertEqual(collection_json["items"][0], annotation["id"])

    def test_store_can_remove_annotation_from_collection(self):
        annotation = self.store.add_annotation(copy.copy(examples["vincent"]))
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.add_annotation_to_collection(annotation['id'], collection_json["id"])
        self.store.remove_annotation_from_collection(annotation["id"], collection_json["id"])
        collection_json = self.store.retrieve_collection(collection_json["id"])
        self.assertEqual(collection_json["total"], 0)

    def test_store_can_remove_annotation_collection(self):
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.delete_collection(collection_json["id"])
        error = None
        try:
            self.store.retrieve_collection(collection_json["id"])
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)




if __name__ == "__main__":
    unittest.main()


