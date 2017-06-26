import copy
import json
import unittest
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection
from models.annotation_container import AnnotationContainer

class TestAnnotationContainer(unittest.TestCase):

    def setUp(self):
        self.collection = AnnotationCollection(copy.copy(example_collections["empty_collection"]))
        self.annotations = [Annotation(copy.copy(examples["vincent"])), Annotation(copy.copy(examples["theo"]))]
        self.label = "Some collection"
        self.base_url = "http://localhost:3000/api/annotations"

    def test_container_can_be_initialized(self):
        container = AnnotationContainer(self.base_url, [], view="PreferMinimalContainer")
        self.assertEqual(container.page_size, 100)
        self.assertEqual(container.num_pages, 0)
        self.assertEqual(container.metadata['id'], container.update_url(self.base_url, {"iris": 1}))

    def test_container_cannot_be_initialized_with_invalid_prefer_type(self):
        error = None
        try:
            AnnotationContainer(self.base_url, [], view="PreferMaximalContainer")
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        self.assertTrue("is not a valid container option", error.message)

    def test_container_cannot_be_initialized_with_non_positive_integer_page_size(self):
        error = None
        try:
            AnnotationContainer(self.base_url, [], page_size="ab")
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)
        error = None
        try:
            AnnotationContainer(self.base_url, [], page_size=0)
        except AnnotationError as err:
            error = err
        self.assertNotEqual(error, None)

    def test_container_can_be_initialized_with_collection(self):
        container = AnnotationContainer(self.base_url, self.collection)
        self.assertEqual(container.page_size, 100)
        self.assertEqual(container.num_pages, 0)
        self.assertEqual(container.metadata['label'], self.collection.label)

    def test_container_can_generate_view(self):
        container = AnnotationContainer(self.base_url, self.collection)
        view = container.view()
        self.assertTrue("http://www.w3.org/ns/ldp.jsonld", view["@context"])
        self.assertTrue("http://www.w3.org/ns/anno.jsonld", view["@context"])
        self.assertEqual(view["total"], 0)
        self.assertTrue("first" not in view.keys())

    def test_non_empty_container_view_has_first_and_last_page_references(self):
        container = AnnotationContainer(self.base_url, self.annotations)
        view = container.view()
        self.assertEqual(view["total"], 2)
        self.assertEqual(type(view["first"]), str)
        self.assertEqual(type(view["last"]), str)

    def test_container_calculates_page_numbers_correctly(self):
        container = AnnotationContainer(self.base_url, self.annotations, page_size=1)
        view = container.view()
        last_url = container.update_url(self.base_url, {"iris": 1, "page": 1})
        self.assertEqual(view["last"], last_url)
        container = AnnotationContainer(self.base_url, self.annotations, page_size=2)
        view = container.view()
        last_url = container.update_url(self.base_url, {"iris": 1, "page": 0})
        self.assertEqual(view["last"], last_url)

    def test_container_can_generate_pages(self):
        container = AnnotationContainer(self.base_url, self.annotations, page_size=1)
        view = container.view_page(page=0)
        self.assertEqual(view["@context"], "http://www.w3.org/ns/anno.jsonld")
        self.assertEqual(view["id"], container.update_url(self.base_url, {"iris": 1, "page": 0}))
        self.assertEqual(view["type"], "AnnotationPage")
        self.assertEqual(view["partOf"]["id"], container.base_url)
        self.assertEqual(view["startIndex"], 0)
        self.assertEqual(view["next"], container.update_url(self.base_url, {"iris": 1, "page": 1}))
        self.assertEqual(len(view["items"]), 1)

    def test_container_generate_page_referencing(self):
        annotations = [Annotation(copy.copy(examples["vincent"])), Annotation(copy.copy(examples["theo"])), Annotation(copy.copy(examples["brothers"]))]
        container = AnnotationContainer(self.base_url, annotations, page_size=1)
        view0 = container.view_page(page=0)
        view1 = container.view_page(page=1)
        view2 = container.view_page(page=2)
        self.assertEqual(view0["next"], view1["id"])
        self.assertEqual(view0["next"], view2["prev"])
        self.assertEqual(view1["prev"], view0["id"])
        self.assertEqual(view1["next"], view2["id"])
        self.assertEqual(view2["prev"], view1["id"])
        items = view0["items"] + view1["items"] + view2["items"]
        for anno in annotations:
            self.assertTrue(anno.id in items)

    def test_container_view_can_show_first_page_as_iris(self):
        anno_ids = [anno.id for anno in self.annotations]
        container = AnnotationContainer(self.base_url, self.annotations, view="PreferContainedIRIs", page_size=1)
        view = container.view()
        self.assertEqual(view["first"]["id"], container.update_url(container.base_url, {"page": 0}))
        self.assertEqual(view["first"]["next"], container.update_url(container.base_url, {"page": 1}))
        self.assertEqual(len(view["first"]["items"]), 1)
        self.assertTrue(view["first"]["items"][0] in anno_ids)

    def test_container_view_can_show_first_page_as_descriptions(self):
        anno = self.annotations[0]
        container = AnnotationContainer(self.base_url, [anno], view="PreferContainedDescriptions")
        view = container.view()
        item = view["first"]["items"][0]
        for key in item.keys():
            self.assertTrue(key in anno.data.keys())
            self.assertEqual(item[key], anno.data[key])


