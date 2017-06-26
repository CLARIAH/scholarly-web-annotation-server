import copy
import unittest
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection

class TestAnnotationCollection(unittest.TestCase):

    def setUp(self):
        self.collection = example_collections["empty_collection"]
        self.label = "Some collection"

    def test_annotation_collection_can_be_initialized(self):
        collection = AnnotationCollection(self.collection)
        self.assertEqual(collection.list_annotations(), [])
        self.assertEqual(collection.label, self.collection["label"])
        self.assertNotEqual(collection.id, None)

    def test_annotation_collection_can_add_valid_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(copy.copy(examples["vincent"]))
        collection.add_annotation(annotation.id)
        self.assertEqual(collection.size(), 1)

    def test_annotation_collection_can_retrieve_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(copy.copy(examples["vincent"]))
        collection.add_annotation(annotation.id)
        self.assertTrue(collection.has_annotation(annotation.id))

    def test_annotation_collection_can_remove_valid_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(copy.copy(examples["vincent"]))
        collection.add_annotation(annotation.id)
        self.assertEqual(collection.has_annotation(annotation.id), True)
        collection.remove_annotation(annotation.id)
        self.assertEqual(collection.has_annotation(annotation.id), False)

    def test_annotation_collection_can_generate_an_annotation_collection_json(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(copy.copy(examples["vincent"]))
        collection.add_annotation(annotation.id)
        collection_json = collection.to_json()
        self.assertEqual(collection_json["id"], collection.id)
        self.assertEqual(collection_json["total"], 1)
        self.assertEqual(collection_json["items"][0], annotation.id)



if __name__ == "__main__":
    unittest.main()


