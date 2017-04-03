import unittest
from vocabulary_store import VocabularyStore, InvalidVocabularyError

class TestVocabularyStore(unittest.TestCase):

    def setUp(self):
        self.vocab_good = "vocabularies/vangoghontology.ttl"
        self.vocab_bad = "vocabularies/test_ontology_invalid.ttl"
        self.vocab_none = "vocabularies/vangoghontology.tt"
        self.vocab_url = "http://localhost:3000/vocabularies/vangoghontology.ttl"

    def test_vocabulary_store_can_be_initialized(self):
        vocabulary_store = VocabularyStore()
        self.assertEqual(vocabulary_store.show_vocabularies(), [])

    def test_vocabulary_store_handles_bad_reference(self):
        vocabulary_store = VocabularyStore()
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_none)
        except FileNotFoundError as e:
            error = e
        self.assertTrue(error != None)

    def test_vocabulary_store_handles_invalid_file(self):
        vocabulary_store = VocabularyStore()
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_bad)
        except InvalidVocabularyError as e:
            error = e
        self.assertTrue(error != None)

    def test_vocabulary_store_handles_valid_file(self):
        vocabulary_store = VocabularyStore()
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_url)
        except FileNotFoundError as e:
            error = e
        self.assertTrue(error == None)
        self.assertTrue(vocabulary_store.has_vocabulary(self.vocab_url))

    def test_vocabulary_store_can_lookup_labels(self):
        vocabulary_store = VocabularyStore()
        vocabulary_store.register_vocabulary(self.vocab_url)
        self.assertNotEqual(vocabulary_store.lookupLabel("Letter"), None)
        self.assertEqual(vocabulary_store.lookupLabel("NotInStore"), None)

    def test_vocabulary_store_handles_imports(self):
        vocabulary_store = VocabularyStore()
        vocabulary_store.register_vocabulary(self.vocab_url)
        self.assertNotEqual(vocabulary_store.lookupLabel("hasPart"), None)


