import unittest
from resource_model import Resource, ResourceStore, InvalidResourceError, InvalidResourceMapError
from vocabulary_store import InvalidVocabularyError


class TestResourceModel(unittest.TestCase):

    def test_resource_cannot_be_initialized_without_parameters(self):
        error = None
        try:
            resource = Resource()
        except InvalidResourceError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_resource_can_be_initialized(self):
        error = None
        try:
            resource = Resource({"resource": "Vincent", "typeof": "van_Gogh"})
        except InvalidResourceError as e:
            error = e
        self.assertEqual(error, None)
        self.assertEqual(resource.typeof, "van_Gogh")
        self.assertEqual(resource.resource, "Vincent")

class TestResourceStore(unittest.TestCase):

    def setUp(self):
        self.vocab_bad = "http://localhost:3000/vocabularies/test_ontology_invalid.ttl"
        self.vocab_none = "http://localhost:3000/vocabularies/vangoghontology.tt"
        self.vocab_url = "http://localhost:3000/vocabularies/vangoghontology.ttl"
        self.valid_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "resource": "urn:vangogh:testletter",
            "typeof": "Letter",
            "hasPart": [
                {
                    "resource": "urn:vangogh:testletter:p.5",
                    "typeof": "ParagraphInLetter"
                }
            ]
        }

    def test_resource_store_can_be_initialized(self):
        store = ResourceStore()
        self.assertEqual(store.resource_index, {})

    def test_resource_store_rejects_resource_map_with_invalid_vocabulary(self):
        resource_map = self.valid_map
        resource_map['vocab'] = self.vocab_bad
        store = ResourceStore()
        error = None
        try:
            store.register_by_map(resource_map)
        except InvalidVocabularyError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_resource_store_can_extract_relations_from_map(self):
        store = ResourceStore()
        store.vocab_store.register_vocabulary(self.vocab_url)
        relations = store.get_resource_relations(self.valid_map)
        self.assertTrue("hasPart" in relations)

    def test_resource_store_accepts_valid_resource_map(self):
        store = ResourceStore()
        error = None
        try:
            store.register_by_map(self.valid_map)
        except InvalidResourceMapError as e:
            error = e
            print(error.message)
        self.assertEqual(error, None)
        self.assertTrue(store.has_resource(self.valid_map["resource"]))


