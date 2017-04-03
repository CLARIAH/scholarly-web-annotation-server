import unittest
from annotation_examples import annotations as examples
from server.annotation import Annotation, AnnotationStore, AnnotationValidator, InvalidAnnotation

class TestAnnotationValidation(unittest.TestCase):

    def test_validator_rejects_invalid_annotation(self):
        validator = AnnotationValidator()
        error = None
        try:
            validator.validate(examples["no_target"])
        except InvalidAnnotation as e:
            error = e
            pass
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_validator_accepts_valid_annotation(self):
        validator = AnnotationValidator()
        self.assertEqual(validator.validate(examples["vincent"]), True)

class TestAnnotation(unittest.TestCase):

    def setUp(self):
        self.annotation = Annotation(examples["vincent"])

    def test_annotation_has_id(self):
        self.assertTrue('id' in self.annotation.data)
        self.assertEqual(self.annotation.id, self.annotation.data['id'])

    def test_annotation_has_creation_timestamp(self):
        self.assertTrue('created' in self.annotation.data)

    def test_annotation_has_type(self):
        self.assertEqual(self.annotation.get_type(), "enrichment")

    def test_annotation_can_update(self):
        update_annotation = examples["vincent"]
        new_motivation = "linking"
        update_annotation['motivation'] = new_motivation
        self.annotation.update(update_annotation)
        # annotation must have 'linking' motivation
        self.assertEqual(self.annotation.data['motivation'], new_motivation)
        # annotation must have a 'modified' timestamp
        self.assertTrue('modified' in self.annotation.data)

class TestAnnotationStore(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()

    def test_store_rejects_invalid_annotation(self):
        error = None
        try:
            self.store.add(examples["no_target"])
        except InvalidAnnotation as e:
            error = e
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_store_accepts_valid_annotation(self):
        error = None
        try:
            self.store.add(examples["vincent"])
        except InvalidAnnotation as e:
            error = e
        # error must be defined
        self.assertEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(len(self.store.ids()), 1)

    def test_store_can_get_annotation_by_id(self):
        self.store.add(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation = self.store.get(annotation_id)
        self.assertEqual(annotation['id'], annotation_id)

    def test_store_can_get_annotation_by_target_id(self):
        self.store.add(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation_data = self.store.get(annotation_id)
        annotation = Annotation(annotation_data)
        target_ids = annotation.get_target_ids()
        for target_id in target_ids:
            target_annotations = self.store.get_by_target(target_id)
            ids = [target_annotation['id'] for target_annotation in target_annotations]
            self.assertTrue(annotation_data['id'] in ids)

    def test_store_can_update_annotation(self):
        self.store.add(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation = self.store.get(annotation_id)
        annotation['motivation'] = "linking"
        updated_annotation = self.store.update(annotation)
        self.assertEqual(updated_annotation['id'], annotation_id)
        self.assertTrue('modified' in updated_annotation)

    def test_store_can_remove_annotation(self):
        self.store.add(examples["vincent"])
        annotation_id = self.store.ids()[0]
        self.assertEqual(len(self.store.ids()), 1)
        annotation = self.store.remove(annotation_id)
        self.assertEqual(len(self.store.ids()), 0)
        self.assertEqual(annotation, examples["vincent"])
        self.assertEqual(len(self.store.target_index.keys()), 0)

if __name__ == "__main__":
    unittest.main()


