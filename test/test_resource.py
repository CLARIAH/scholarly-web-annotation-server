import unittest
from server_models.resource import Resource, ResourceStore, InvalidResourceError, InvalidResourceMapError
from server_models.vocabulary import InvalidVocabularyError


class TestResourceModel(unittest.TestCase):

    def test_resource_cannot_be_initialized_without_parameters(self):
        error = None
        try:
            Resource()
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
        self.letter_map = {
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
        resource_map = self.letter_map
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
        relations = store.get_resource_relations(self.letter_map)
        self.assertTrue("hasPart" in relations)

    def test_resource_store_accepts_valid_resource_map(self):
        store = ResourceStore()
        error = None
        try:
            store.register_by_map(self.letter_map)
        except InvalidResourceMapError as e:
            error = e
        self.assertEqual(error, None)
        self.assertTrue(store.has_resource(self.letter_map["resource"]))

    def test_resource_store_alerts_registering_known_resources(self):
        store = ResourceStore()
        response = store.register_by_map(self.letter_map)
        self.assertTrue(self.letter_map["resource"] in response["registered"])
        response = store.register_by_map(self.letter_map)
        self.assertEqual(response["registered"], [])
        self.assertTrue(self.letter_map["resource"] in response["ignored"])

    def test_resource_store_alerts_registering_known_resource_as_different_type(self):
        error = None
        store = ResourceStore()
        store.register_by_map(self.letter_map)
        self.letter_map["typeof"] = "Correspondence"
        try:
            store.register_by_map(self.letter_map)
        except InvalidResourceMapError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Conflicting resource types: resource urn:vangogh:testletter is already registered as type Letter and cannot be additionally registered as type Correspondence" % ())

    def test_resource_store_can_link_resource_to_multiple_parents(self):
        self.correspondence_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "resource": "urn:vangogh:correspondence",
            "typeof": "Correspondence",
            "hasPart": [
                {
                    "resource": "urn:vangogh:testletter",
                    "typeof": "Letter"
                }
            ]
        }
        self.collection_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "resource": "urn:vangogh:collection",
            "typeof": "Correspondence",
            "hasPart": [
                {
                    "resource": "urn:vangogh:testletter",
                    "typeof": "Letter"
                }
            ]
        }
        store = ResourceStore()
        response = store.register_by_map(self.letter_map)
        response = store.register_by_map(self.correspondence_map)
        self.assertTrue("urn:vangogh:testletter" in response["ignored"])
        self.assertTrue("urn:vangogh:correspondence" in response["registered"])
        response = store.register_by_map(self.collection_map)
        self.assertTrue("urn:vangogh:testletter" in response["ignored"])
        self.assertTrue("urn:vangogh:collection" in response["registered"])

    def test_resource_store_rejects_resource_of_unknown_type(self):
        error = None
        self.letter_map["typeof"] = "UnknownType"
        store = ResourceStore()
        try:
            store.register_by_map(self.letter_map)
        except InvalidResourceMapError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Illegal resource type: UnknownType")

