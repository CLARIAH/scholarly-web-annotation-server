import os
import unittest
import tempfile
from server_models.resource import Resource, ResourceStore, ResourceError
from server_models.vocabulary import VocabularyError

tempfiles = []

def make_tempfile():
    _, fname = tempfile.mkstemp()
    tempfiles.append(fname)
    return fname

def remove_tempfiles():
    for tempfile in tempfiles:
        try:
            os.unlink(tempfile)
        except FileNotFoundError:
            pass


class TestResourceModel(unittest.TestCase):

    def setUp(self):
        self.letter = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "id": "urn:vangogh:testletter",
            "type": "Letter",
        }
        self.paragraph = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "id": "urn:vangogh:testletter:p.5",
            "type": "ParagraphInLetter"
        }

    def tearDown(self):
        remove_tempfiles()

    def test_resource_cannot_be_initialized_without_parameters(self):
        error = None
        try:
            Resource()
        except ResourceError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_resource_canont_be_initialized_without_required_properties(self):
        error = None
        try:
            Resource({"id": "Vincent"})
        except ResourceError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_resource_can_be_initialized(self):
        error = None
        try:
            resource = Resource(self.letter)
        except ResourceError as e:
            error = e
        self.assertEqual(error, None)
        self.assertEqual(resource.type, self.letter["type"])
        self.assertEqual(resource.id, self.letter["id"])

    def test_resource_accepts_new_subresources(self):
        resource = Resource(self.letter)
        subresource = Resource(self.paragraph)
        error = None
        try:
            resource.add_subresources({"hasPart": [ subresource ]})
        except ResourceError as e:
            error = e
        self.assertEqual(error, None)

class TestResourceStore(unittest.TestCase):

    def setUp(self):
        self.vocab_bad = "http://localhost:3000/vocabularies/test_ontology_invalid.ttl"
        self.vocab_none = "http://localhost:3000/vocabularies/vangoghontology.tt"
        self.vocab_url = "http://localhost:3000/vocabularies/vangoghontology.ttl"
        self.config = {
            "resource_file": make_tempfile(),
            "triple_file": make_tempfile(),
            "url_file": make_tempfile()
        }
        self.letter_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "id": "urn:vangogh:testletter",
            "type": "Letter",
            "hasPart": [
                {
                    "id": "urn:vangogh:testletter:p.5",
                    "type": "ParagraphInLetter"
                }
            ]
        }
        self.correspondence_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "id": "urn:vangogh:correspondence",
            "type": "Correspondence",
            "hasPart": [
                {
                    "id": "urn:vangogh:testletter",
                    "type": "Letter"
                }
            ]
        }
        self.collection_map = {
            "vocab": "http://localhost:3000/vocabularies/vangoghontology.ttl",
            "id": "urn:vangogh:collection",
            "type": "Correspondence",
            "hasPart": [
                {
                    "id": "urn:vangogh:testletter",
                    "type": "Letter"
                }
            ]
        }

    def tearDown(self):
        remove_tempfiles()

    def test_resource_store_can_be_initialized(self):
        store = ResourceStore(self.config)
        self.assertEqual(store.resource_index, {})

    def test_resource_store_rejects_resource_map_with_invalid_vocabulary(self):
        resource_map = self.letter_map
        resource_map['vocab'] = self.vocab_bad
        store = ResourceStore(self.config)
        error = None
        try:
            store.register_by_map(resource_map)
        except VocabularyError as e:
            error = e
        self.assertNotEqual(error, None)

    def test_resource_store_can_extract_relations_from_map(self):
        store = ResourceStore(self.config)
        store.vocab_store.register_vocabulary(self.vocab_url)
        relations = store.get_resource_relations(self.letter_map)
        self.assertTrue("hasPart" in relations)

    def test_resource_store_accepts_valid_resource_map(self):
        store = ResourceStore(self.config)
        error = None
        try:
            store.register_by_map(self.letter_map)
        except ResourceError as e:
            error = e
        self.assertEqual(error, None)
        self.assertTrue(store.has_resource(self.letter_map["id"]))

    def test_resource_store_alerts_registering_known_resources(self):
        store = ResourceStore(self.config)
        response = store.register_by_map(self.letter_map)
        self.assertTrue(self.letter_map["id"] in response["registered"])
        response = store.register_by_map(self.letter_map)
        self.assertEqual(response["registered"], [])
        self.assertTrue(self.letter_map["id"] in response["ignored"])

    def test_resource_store_alerts_registering_known_resource_as_different_type(self):
        error = None
        store = ResourceStore(self.config)
        store.register_by_map(self.letter_map)
        self.letter_map["type"] = "Correspondence"
        try:
            store.register_by_map(self.letter_map)
        except ResourceError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Conflicting resource types: resource urn:vangogh:testletter is already registered as type Letter and cannot be additionally registered as type Correspondence" % ())

    def test_resource_store_can_link_resource_to_multiple_parents(self):
        store = ResourceStore(self.config)
        response = store.register_by_map(self.letter_map)
        response = store.register_by_map(self.correspondence_map)
        self.assertTrue("urn:vangogh:testletter" in response["ignored"])
        self.assertTrue("urn:vangogh:correspondence" in response["registered"])
        response = store.register_by_map(self.collection_map)
        self.assertTrue("urn:vangogh:testletter" in response["ignored"])
        self.assertTrue("urn:vangogh:collection" in response["registered"])

    def test_resource_store_rejects_resource_of_unknown_type(self):
        error = None
        self.letter_map["type"] = "UnknownType"
        store = ResourceStore(self.config)
        try:
            store.register_by_map(self.letter_map)
        except ResourceError as e:
            error = e
        self.assertNotEqual(error, None)
        self.assertEqual(error.message, "Illegal resource type: UnknownType")

    def test_resource_store_returns_indirectly_connected_resources(self):
        store = ResourceStore(self.config)
        store.register_by_map(self.letter_map)
        store.register_by_map(self.correspondence_map)
        resource = store.get_resource(self.correspondence_map["id"])
        self.assertTrue("urn:vangogh:testletter:p.5" in resource.list_members())

    def test_resource_store_can_persist_data(self):
        store1 = ResourceStore(self.config)
        store1.register_by_map(self.letter_map)
        store1.save_index()
        store2 = ResourceStore(self.config)
        self.assertEqual(store1.resource_index.keys(), store2.resource_index.keys())

    def test_resource_store_can_generate_map_of_complex_resource(self):
        store = ResourceStore(self.config)
        store.register_by_map(self.letter_map)
        store.register_by_map(self.correspondence_map)
        correspondence_map = store.generate_resource_map(self.correspondence_map["id"])
        letter_map = correspondence_map["hasPart"][0]
        paragraph_map = letter_map["hasPart"][0]
        self.assertEqual(correspondence_map["id"], self.correspondence_map["id"])
        self.assertEqual(letter_map["id"], self.letter_map["id"])
        self.assertEqual(letter_map["id"], self.letter_map["id"])

