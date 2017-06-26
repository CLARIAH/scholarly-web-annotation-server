import uuid
import copy
import unittest
from annotation_examples import annotations as examples
from models.annotation import Annotation, WebAnnotationValidator, AnnotationError

class TestAnnotationValidation(unittest.TestCase):

    def setUp(self):
        self.validator = WebAnnotationValidator()

    def test_validator_rejects_invalid_annotation(self):
        error = None
        try:
            self.validator.validate(examples["no_target"], "Annotation")
        except AnnotationError as e:
            error = e
            pass
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_validator_accepts_valid_annotation(self):
        self.assertEqual(self.validator.validate(copy.copy(examples["vincent"]), "Annotation"), True)

    def test_validator_accepts_valid_annotation_page(self):
        page = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationPage",
            "items": [
                {
                    "id": uuid.uuid4().urn,
                    "body": "some body",
                    "target": "http://some.target.com/"
                }
            ],
            "startIndex": 0
        }
        error = None
        try:
            validation_status = self.validator.validate(page, "AnnotationPage")
        except AnnotationError as e:
            error = e
        self.assertEqual(error, None)
        self.assertEqual(validation_status, True)

    def test_validator_rejects_empty_annotation_page(self):
        page = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationPage",
            "items": [
            ],
            "startIndex": 0
        }
        error = None
        try:
            self.validator.validate(page, "AnnotationPage")
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_validator_rejects_invalid_annotation_page(self):
        page = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationPage",
            "startIndex": 0
        }
        error = None
        try:
            self.validator.validate(page, "AnnotationPage")
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertTrue('MUST have an "items" property' in error.message)

    def test_validator_accepts_valid_annotation_collection(self):
        page_id = uuid.uuid4().urn
        collection = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationCollection",
            "label": "Some collection",
            "total": 1,
            "first": page_id,
            "last": page_id,
        }
        error = None
        try:
            self.validator.validate(collection, "AnnotationCollection")
        except AnnotationError as e:
            error = e
        self.assertEqual(error, None)

    def test_validator_accepts_empty_annotation_collection(self):
        collection = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationCollection",
            "label": "Some collection",
        }
        error = None
        try:
            self.validator.validate(collection, "AnnotationCollection")
        except AnnotationError as e:
            error = e
        self.assertEqual(error, None)

    def test_validator_rejects_invalid_annotation_collection(self):
        collection = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "type": "AnnotationCollection",
            "label": "Some collection",
            "total": 1,
        }
        error = None
        try:
            self.validator.validate(collection, "AnnotationCollection")
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertTrue('Non-empty collection MUST have "first" property referencing the first AnnotationPage')

class TestAnnotation(unittest.TestCase):

    def setUp(self):
        self.annotation = Annotation(copy.copy(examples["vincent"]))

    def test_annotation_has_id(self):
        self.assertTrue('id' in self.annotation.data)
        self.assertEqual(self.annotation.id, self.annotation.data['id'])

    def test_annotation_has_creation_timestamp(self):
        self.assertTrue('created' in self.annotation.data)

    def test_annotation_can_update(self):
        update_annotation = self.annotation.data
        new_motivation = "linking"
        update_annotation['motivation'] = new_motivation
        self.annotation.update(update_annotation)
        # annotation must have 'linking' motivation
        self.assertEqual(self.annotation.data['motivation'], new_motivation)
        # annotation must have a 'modified' timestamp
        self.assertTrue('modified' in self.annotation.data)

if __name__ == "__main__":
    unittest.main()


