import unittest
import copy
import os
import json, string, random
import tempfile
import annotation_server as server
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation_store import AnnotationStore
from models.resource import ResourceStore

tempfiles = []

def make_tempfile():
    _, fname = tempfile.mkstemp()
    tempfiles.append(fname)
    return fname

def remove_tempfiles():
    global tempfiles
    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except FileNotFoundError:
            print("cannot remove temp files")
            pass
    tempfiles = []


def get_json(response):
    return json.loads(response.get_data(as_text=True))

def add_example(app):
    annotation = copy.copy(examples["vincent"])
    response = app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
    return get_json(response)

class TestAnnotationAPI(unittest.TestCase):

    def setUp(self):
        annotations_file = make_tempfile()
        server.annotation_store = AnnotationStore() # always start with empty store
        self.temp_index_name = "test-index-%s" % (''.join(random.choices(string.ascii_lowercase + string.digits, k=16)))
        self.config = {
            "host": "localhost",
            "port": 9200,
            "index": self.temp_index_name,
            "page_size": 1000
        }
        server.annotation_store.configure_index(self.config)
        server.app.config['DATAFILE'] = annotations_file
        self.app = server.app.test_client()

    def tearDown(self):
        remove_tempfiles()
        # make sure to remove temp index
        server.annotation_store.es.indices.delete(self.temp_index_name)

    def test_POST_annotation_returns_annotation_with_id(self):
        annotation = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
        stored = get_json(response)
        self.assertTrue('id' in stored)
        self.assertTrue('created' in stored)

    def test_GET_annotation_returns_stored_annotation(self):
        example = add_example(self.app)
        response = self.app.get("/api/annotations/" + example['id'])
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])

    def test_GET_annotations_returns_annotation_container(self):
        headers = {"Prefer": 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedDescriptions"'}
        example = add_example(self.app)
        server.annotation_store.es.indices.refresh(self.temp_index_name)
        response = self.app.get('/api/annotations')
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(container["total"], 1)

    def test_GET_annotations_with_descriptions_returns_container_with_descriptions(self):
        add_example(self.app)
        server.annotation_store.es.indices.refresh(self.temp_index_name)
        response = self.app.get('/api/annotations', headers={"Prefer": 'return=representation;include="http://www.w3.org/ns/ldp#PreferContainedDescriptions"'})
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(len(container["first"]["items"]), 1)
        self.assertEqual(container["total"], 1)

    def test_PUT_annotation_returns_modified_annotation(self):
        example = add_example(self.app)
        example["motivation"] = "linking"
        response = self.app.put("/api/annotations/" + example['id'], data=json.dumps(example), content_type="application/json")
        annotation = get_json(response)
        self.assertTrue('modified' in annotation)
        self.assertEqual(annotation['motivation'], example['motivation'])

    def test_DELETE_annotation_returns_removed_annotation(self):
        example = add_example(self.app)
        response = self.app.delete("/api/annotations/" + example['id'])
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])
        response = self.app.get("/api/annotations/" + example['id'])
        self.assertEqual(response.status_code, 404)

"""
class TestAnnotationAPIResourceEndpoints(unittest.TestCase):

    def setUp(self):
        annotations_file = make_tempfile()
        server.annotation_store = AnnotationStore() # always start with empty store
        self.temp_index_name = "test-index-%s" % (''.join(random.choices(string.ascii_lowercase + string.digits, k=16)))
        self.config = {
            "host": "localhost",
            "port": 9200,
            "index": self.temp_index_name,
            "page_size": 1000
        }
        print("creating index", self.temp_index_name)
        server.annotation_store.configure_index(self.config)
        resource_config = {
            "resource_file": make_tempfile(),
            "triple_file": make_tempfile(),
            "url_file": make_tempfile()
        }
        server.resource_store = ResourceStore(resource_config)
        server.app.config['DATAFILE'] = annotations_file
        self.app = server.app.test_client()
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
        self.annotation = {
            "type": "Annotation",
            "motivation": "classifying",
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "target": [
                {
                    "type": "Text",
                    "selector": None,
                    "source": "urn:vangogh:testletter:p.5"
                }
            ],
            "body": [
                {
                    "value": "Location identifier",
                    "type": "classification",
                    "purpose": "classifying",
                    "id": "http://dbpedia.org/resource/Location_identifier",
                    "vocabulary": "DBpedia"
                }
            ],
            "creator": "marijn",
        }

    def tearDown(self):
        remove_tempfiles()
        print("removing index", self.temp_index_name)
        server.annotation_store.es.indices.delete(self.temp_index_name)

    def test_api_can_accepts_valid_resource(self):
        response = self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        data = get_json(response)
        self.assertTrue(self.letter_map["id"] in data["registered"])

    def test_api_rejects_invalid_resource(self):
        self.letter_map["type"] = "Collection"
        response = self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        data = get_json(response)
        self.assertEqual(data["message"], "Illegal resource type: Collection")
        self.assertEqual(data["status_code"], 400)

    def test_api_can_return_registered_resource(self):
        self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        response = self.app.get("/api/resources/%s" % (self.letter_map["id"]))
        data = get_json(response)
        self.assertEqual(data["id"], self.letter_map["id"])
        self.assertEqual(data["type"], self.letter_map["type"])
        self.assertTrue("registered" in data.keys())

    def test_api_returns_error_for_unknown_resource(self):
        response = self.app.get("/api/resources/%s" % (self.letter_map["id"]))
        self.assertEqual(response.status_code, 400)
        data = get_json(response)
        self.assertEqual(data["message"], "unknown resource")

    def test_api_can_return_registered_resource_map(self):
        self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        response = self.app.get("/api/resources/%s/structure" % (self.letter_map["id"]))
        data = get_json(response)
        self.assertEqual(data["id"], self.letter_map["id"])
        self.assertEqual(data["type"], self.letter_map["type"])
        self.assertEqual(data.keys(), self.letter_map.keys())

    def test_api_can_register_map_for_known_resource(self):
        response = self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        data = get_json(response)
        response = self.app.post("/api/resources/%s/structure" % (self.letter_map["id"]), data=json.dumps(self.letter_map), content_type="application/json")
        data = get_json(response)
        self.assertTrue("registered" in data.keys())
        self.assertEqual(data["registered"], [])
        self.assertEqual(len(data["ignored"]), 2)

    def test_api_can_return_registered_resource_annotations(self):
        self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        response = self.app.post("/api/annotations", data=json.dumps(self.annotation), content_type="application/json")
        stored_annotation = get_json(response)
        response = self.app.get("/api/resources/%s/annotations" % (self.letter_map["id"]))
        annotations = get_json(response)
        self.assertEqual(annotations[0]["id"], stored_annotation["id"])
"""

class TestAnnotationAPICollectionEndpoints(unittest.TestCase):

    def setUp(self):
        annotations_file = make_tempfile()
        server.annotation_store = AnnotationStore() # always start with empty store
        self.temp_index_name = "test-index-%s" % (''.join(random.choices(string.ascii_lowercase + string.digits, k=16)))
        self.config = {
            "host": "localhost",
            "port": 9200,
            "index": self.temp_index_name,
            "page_size": 1000
        }
        server.annotation_store.configure_index(self.config)
        server.app.config['DATAFILE'] = annotations_file
        self.app = server.app.test_client()

    def tearDown(self):
        remove_tempfiles()
        server.annotation_store.es.indices.delete(self.temp_index_name)

    def test_api_can_create_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertTrue("id" in collection_registered)
        self.assertEqual(collection_registered["label"], collection_raw["label"])
        self.assertEqual(collection_registered["creator"], collection_raw["creator"])

    def test_api_can_retrieve_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]))
        collection_retrieved = get_json(response)
        self.assertEqual(response.status_code, 200)
        for key in collection_retrieved.keys():
            self.assertEqual(collection_retrieved[key], collection_registered[key])

    def test_api_can_update_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        collection_registered["label"] = "New label"
        response = self.app.put("/api/collections/%s" % (collection_registered["id"]), data=json.dumps(collection_registered), content_type="application/json")
        collection_updated = get_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(collection_updated["label"], collection_registered["label"])
        self.assertTrue("modified" in collection_updated)

    def test_api_can_delete_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        response = self.app.delete("/api/collections/%s" % (collection_registered["id"]))
        collection_deleted = get_json(response)
        self.assertEqual(collection_registered["id"], collection_deleted["id"])
        self.assertEqual(collection_deleted["status"], "deleted")
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]))
        self.assertEqual(response.status_code, 404)

    def test_api_can_add_annotation_to_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        self.assertEqual(collection_registered["total"], 0)
        annotation_raw = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation_raw), content_type="application/json")
        annotation_registered = get_json(response)
        headers = {"Prefer": 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedIRIs"'}
        response = self.app.post("/api/collections/%s/annotations/" % (collection_registered["id"]), data=json.dumps(annotation_registered), content_type="application/json", headers=headers)
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]), headers=headers)
        collection_retrieved = get_json(response)
        self.assertEqual(collection_retrieved["total"], 1)
        self.assertEqual(collection_retrieved["first"]["items"][0], annotation_registered["id"])

    def test_api_can_remove_annotation_from_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        collection_registered = get_json(response)
        self.assertEqual(collection_registered["total"], 0)
        annotation_raw = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation_raw), content_type="application/json")
        annotation_registered = get_json(response)
        response = self.app.post("/api/collections/%s/annotations/" % (collection_registered["id"]), data=json.dumps(annotation_registered), content_type="application/json")
        response = self.app.delete("/api/collections/%s/annotations/%s" % (collection_registered["id"], annotation_registered["id"]))
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]))
        collection_retrieved = get_json(response)
        self.assertEqual(collection_retrieved["total"], 0)


if __name__ == "__main__":
    pass
    #unittest.main()


