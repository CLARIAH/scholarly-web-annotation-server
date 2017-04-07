import tempfile
import unittest
from server_models.vocabulary import VocabularyStore, VocabularyError

def make_tempfile():
    _, fname = tempfile.mkstemp()
    return fname

class TestVocabularyStore(unittest.TestCase):

    def setUp(self):
        self.vocab_good = "vocabularies/vangoghontology.ttl"
        self.vocab_bad = "vocabularies/test_ontology_invalid.ttl"
        self.vocab_none = "vocabularies/vangoghontology.tt"
        self.vocab_url = "http://localhost:3000/vocabularies/vangoghontology.ttl"
        self.config = {
            "triple_file": make_tempfile(),
            "url_file": make_tempfile()
        }

    def test_vocabulary_store_can_be_initialized(self):
        vocabulary_store = VocabularyStore(self.config)
        self.assertEqual(vocabulary_store.show_vocabularies(), [])

    def test_vocabulary_store_handles_bad_reference(self):
        vocabulary_store = VocabularyStore(self.config)
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_none)
        except FileNotFoundError as e:
            error = e
        self.assertTrue(error != None)

    def test_vocabulary_store_handles_invalid_file(self):
        vocabulary_store = VocabularyStore(self.config)
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_bad)
        except VocabularyError as e:
            error = e
        self.assertTrue(error != None)

    def test_vocabulary_store_handles_valid_file(self):
        vocabulary_store = VocabularyStore(self.config)
        error = None
        try:
            vocabulary_store.register_vocabulary(self.vocab_url)
        except FileNotFoundError as e:
            error = e
        self.assertTrue(error == None)
        self.assertTrue(vocabulary_store.has_vocabulary(self.vocab_url))

    def test_vocabulary_store_can_lookup_labels(self):
        vocabulary_store = VocabularyStore(self.config)
        vocabulary_store.register_vocabulary(self.vocab_url)
        self.assertNotEqual(vocabulary_store.lookupLabel("Letter"), None)
        self.assertEqual(vocabulary_store.lookupLabel("NotInStore"), None)

    def test_vocabulary_store_handles_imports(self):
        vocabulary_store = VocabularyStore(self.config)
        vocabulary_store.register_vocabulary(self.vocab_url)
        self.assertNotEqual(vocabulary_store.lookupLabel("hasPart"), None)

    def test_vocabulary_store_can_save_and_load_urls(self):
        store1 = VocabularyStore(self.config)
        store1.register_vocabulary(self.vocab_url)
        store1.save_urls()
        store2 = VocabularyStore(self.config)
        self.assertEqual(store1.show_vocabularies(), store2.show_vocabularies())

    def test_vocabulary_store_can_save_and_load_store(self):
        store1 = VocabularyStore(self.config)
        store1.register_vocabulary(self.vocab_url)
        store1.save_store()
        store2 = VocabularyStore(self.config)
        triples1 = [t for t in store1.vocab.triples( (None, None, None) )]
        triples2 = [t for t in store2.vocab.triples( (None, None, None) )]
        self.assertEqual(len(triples1), len(triples2))




