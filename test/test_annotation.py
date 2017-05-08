import uuid
import unittest
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationStore, AnnotationCollection, AnnotationPage, WebAnnotationValidator, InvalidAnnotation, AnnotationError

class TestAnnotationValidation(unittest.TestCase):

    def setUp(self):
        self.validator = WebAnnotationValidator()

    def test_validator_rejects_invalid_annotation(self):
        error = None
        try:
            self.validator.validate(examples["no_target"], "Annotation")
        except InvalidAnnotation as e:
            error = e
            pass
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_validator_accepts_valid_annotation(self):
        self.assertEqual(self.validator.validate(examples["vincent"], "Annotation"), True)

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
        except InvalidAnnotation as e:
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
        except InvalidAnnotation as e:
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
        except InvalidAnnotation as e:
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
        except InvalidAnnotation as e:
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
        except InvalidAnnotation as e:
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
        except InvalidAnnotation as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertTrue('Non-empty collection MUST have "first" property referencing the first AnnotationPage')

class TestAnnotation(unittest.TestCase):

    def setUp(self):
        self.annotation = Annotation(examples["vincent"])

    def test_annotation_has_id(self):
        self.assertTrue('id' in self.annotation.data)
        self.assertEqual(self.annotation.id, self.annotation.data['id'])

    def test_annotation_has_creation_timestamp(self):
        self.assertTrue('created' in self.annotation.data)

    def test_annotation_can_update(self):
        update_annotation = examples["vincent"]
        new_motivation = "linking"
        update_annotation['motivation'] = new_motivation
        self.annotation.update(update_annotation)
        # annotation must have 'linking' motivation
        self.assertEqual(self.annotation.data['motivation'], new_motivation)
        # annotation must have a 'modified' timestamp
        self.assertTrue('modified' in self.annotation.data)

class TestAnnotationCollection(unittest.TestCase):

    def setUp(self):
        self.collection = example_collections["empty_collection"]
        self.label = "Some collection"

    def test_annotation_collection_can_be_initialized(self):
        collection = AnnotationCollection(self.collection)
        self.assertEqual(collection.total, 0)
        self.assertEqual(collection.label, self.collection["label"])
        self.assertNotEqual(collection.id, None)

    def test_annotation_collection_can_add_valid_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(examples["vincent"])
        new_pages = collection.add_existing(annotation)
        self.assertEqual(collection.total, 1)
        self.assertNotEqual(new_pages, None)

    def test_annotation_collection_can_retrieve_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(examples["vincent"])
        new_pages = collection.add_existing(annotation)
        retrieved = collection.get(annotation.id)
        self.assertEqual(annotation.id, retrieved["id"])

    def test_annotation_collection_can_remove_valid_annotation(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(examples["vincent"])
        new_pages = collection.add_existing(annotation)
        self.assertEqual(collection.total, 1)
        collection.remove(annotation.id)
        self.assertEqual(collection.total, 0)
        error = None
        try:
            collection.get(annotation.id)
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_annotation_collection_can_generate_an_annotation_page_json(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(examples["vincent"])
        new_pages = collection.add_existing(annotation)
        page_json = collection.get_page_json(new_pages[0])
        self.assertEqual(page_json["id"], new_pages[0])
        self.assertEqual(page_json["items"][0]["id"], annotation.id)

    def test_annotation_collection_can_generate_an_annotation_collection_json(self):
        collection = AnnotationCollection(self.collection)
        annotation = Annotation(examples["vincent"])
        collection.add_existing(annotation)
        collection_json = collection.to_json()
        self.assertEqual(collection_json["id"], collection.id)
        self.assertEqual(collection_json["total"], 1)
        self.assertEqual(collection_json["first"], collection.first)
        self.assertEqual(collection_json["last"], collection.last)
        self.assertEqual(collection_json["first"], collection_json["last"])

class TestAnnotationPage(unittest.TestCase):

    def test_annotation_page_can_be_initialised(self):
        collection_id = uuid.uuid4().urn
        page = AnnotationPage(collection_id)
        self.assertEqual(page.part_of, collection_id)
        self.assertNotEqual(page.id, None)

    def test_non_full_annotation_page_can_add_valid_annotation(self):
        collection_id = uuid.uuid4().urn
        annotations = [examples["vincent"]]
        page = AnnotationPage(collection_id, annotations=annotations)
        self.assertEqual(page.start_index, 0)
        self.assertEqual(len(page.annotations), 1)

    def test_annotation_page_cannot_be_initialised_with_more_than_page_size(self):
        collection_id = uuid.uuid4().urn
        annotations = [examples["vincent"], examples["theo"]]
        error = None
        try:
            page = AnnotationPage(collection_id, page_size=1, annotations=annotations)
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_annotation_page_adds_at_most_page_size(self):
        collection_id = uuid.uuid4().urn
        annotations = [examples["vincent"], examples["theo"]]
        page = AnnotationPage(collection_id, page_size=1)
        remaining = page.add(annotations)
        self.assertEqual(page.start_index, 0)
        self.assertEqual(len(page.annotations), 1)
        self.assertEqual(len(remaining), 1)

    def test_annotation_page_can_set_next_page_id(self):
        collection_id = uuid.uuid4().urn
        annotations = [examples["vincent"]]
        page1 = AnnotationPage(collection_id, page_size=1, annotations=annotations)
        start_index = page1.start_index + len(page1.annotations)
        page2 = AnnotationPage(collection_id, annotations=annotations, prev_id=page1.id, start_index=start_index)
        page1.set_next(page2.id)
        self.assertEqual(page2.prev_id, page1.id)
        self.assertEqual(page1.next_id, page2.id)

    def test_annotation_page_with_prev_cannot_be_initialised_without_start_index(self):
        collection_id = uuid.uuid4().urn
        annotations = []
        page1 = AnnotationPage(collection_id, annotations=annotations)
        error = None
        try:
            page2 = AnnotationPage(collection_id, annotations=annotations, prev_id=page1.id)
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertTrue("start_index has to be defined and higher than zero" in error.message)

    def test_second_annotation_page_has_correct_start_index(self):
        collection_id = uuid.uuid4().urn
        annotations = [examples["vincent"], examples["theo"]]
        page1 = AnnotationPage(collection_id, page_size=1)
        remaining = page1.add(annotations)
        start_index = page1.start_index + len(page1.annotations)
        page2 = AnnotationPage(collection_id, page_size=1, prev_id=page1.id, start_index=start_index)
        self.assertEqual(len(remaining), 1)
        self.assertEqual(page1.start_index, 0)
        remaining = page2.add(remaining)
        self.assertEqual(len(remaining), 0)
        self.assertEqual(page2.start_index, 1)

    def test_annotation_page_can_remove_annotation(self):
        collection_id = uuid.uuid4().urn
        annotation = Annotation(examples["vincent"])
        page = AnnotationPage(collection_id, page_size=1)
        page.add(annotation)
        page.remove(annotation.id)
        self.assertEqual(len(page.annotations), 0)

    def test_annotation_page_warns_annotation_is_not_on_page(self):
        collection_id = uuid.uuid4().urn
        annotations = [Annotation(examples["vincent"]), Annotation(examples["theo"])]
        page = AnnotationPage(collection_id, page_size=1)
        page.add(annotations[0])
        error = None
        try:
            page.get(annotations[1].id)
        except AnnotationError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertTrue("Annotation Page does not contain annotation with id" in error.message)

class TestAnnotationStore(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()

    def test_store_rejects_invalid_annotation(self):
        error = None
        try:
            self.store.add_annotation(examples["no_target"])
        except InvalidAnnotation as e:
            error = e
        # error must be defined
        self.assertNotEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(error.message, 'annotation MUST have at least one target')

    def test_store_accepts_valid_annotation(self):
        error = None
        try:
            self.store.add_annotation(examples["vincent"])
        except InvalidAnnotation as e:
            error = e
        # error must be defined
        self.assertEqual(error, None)
        # error must indicate annotation lacks target
        self.assertEqual(len(self.store.ids()), 1)

    def test_store_can_get_annotation_by_id(self):
        self.store.add_annotation(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation = self.store.get(annotation_id)
        self.assertEqual(annotation['id'], annotation_id)

    def test_store_can_get_annotation_by_target_id(self):
        self.store.add_annotation(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation_data = self.store.get(annotation_id)
        annotation = Annotation(annotation_data)
        target_ids = annotation.get_target_ids()
        for target_id in target_ids:
            target_annotations = self.store.get_by_target(target_id)
            ids = [target_annotation['id'] for target_annotation in target_annotations]
            self.assertTrue(annotation_data['id'] in ids)

    def test_store_can_update_annotation(self):
        self.store.add_annotation(examples["vincent"])
        annotation_id = self.store.ids()[0]
        annotation = self.store.get(annotation_id)
        annotation['motivation'] = "linking"
        updated_annotation = self.store.update(annotation)
        self.assertEqual(updated_annotation['id'], annotation_id)
        self.assertTrue('modified' in updated_annotation)

    def test_store_can_remove_annotation(self):
        self.store.add_annotation(examples["vincent"])
        annotation_id = self.store.ids()[0]
        self.assertEqual(len(self.store.ids()), 1)
        annotation = self.store.remove(annotation_id)
        self.assertEqual(len(self.store.ids()), 0)
        self.assertEqual(annotation, examples["vincent"])
        self.assertEqual(len(self.store.target_index.keys()), 0)

    def test_store_can_add_annotation_collection(self):
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.assertEqual(collection_json["label"], collection_data["label"])
        self.assertNotEqual(collection_json["id"], None)

    def test_store_can_add_annotation_to_collection(self):
        annotation = self.store.add_annotation(examples["vincent"])
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.add_annotation_to_collection(annotation["id"], collection_json["id"])
        collection_json = self.store.retrieve_collection(collection_json["id"])
        self.assertEqual(collection_json["total"], 1)
        page_json = self.store.retrieve_collection_page(collection_json["first"])
        self.assertEqual(len(page_json["items"]), 1)
        self.assertEqual(page_json["items"][0]["id"], annotation["id"])

    def test_store_can_remove_annotation_from_collection(self):
        annotation = self.store.add_annotation(examples["vincent"])
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.add_annotation_to_collection(annotation["id"], collection_json["id"])
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

    def test_store_removes_annotation_collection_with_pages(self):
        annotation = self.store.add_annotation(examples["vincent"])
        collection_data = example_collections["empty_collection"]
        collection_json = self.store.create_collection(collection_data)
        self.store.add_annotation_to_collection(annotation["id"], collection_json["id"])
        collection_json = self.store.retrieve_collection(collection_json["id"])
        self.assertEqual(len(self.store.page_index.keys()), 1)
        self.store.delete_collection(collection_json["id"])
        self.assertEqual(len(self.store.page_index.keys()), 0)

if __name__ == "__main__":
    unittest.main()


