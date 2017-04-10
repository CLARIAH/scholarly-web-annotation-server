import unittest
import os
import json
import tempfile
import server as server
from annotation_examples import annotations as examples
from server_models.resource import ResourceStore

tempfiles = []

def make_tempfile():
    _, fname = tempfile.mkstemp()
    tempfiles.append(fname)
    return fname

def remove_tempfiles():
    for tmpfile in tempfiles:
        try:
            os.unlink(tmpfile)
        except FileNotFoundError:
            pass


def get_json(response):
    return json.loads(response.get_data(as_text=True))

def add_example(app):
    annotation = examples["vincent"]
    response = app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
    return get_json(response)

class TestAnnotationAPI(unittest.TestCase):

    def setUp(self):
        annotations_file = make_tempfile()
        server.app.config['DATAFILE'] = annotations_file
        self.app = server.app.test_client()

    def tearDown(self):
        remove_tempfiles()
        #os.unlink(server.app.config['DATAFILE'])

    def test_POST_annotation_returns_annotation_with_id(self):
        annotation = examples["vincent"]
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
        stored = get_json(response)
        self.assertTrue('id' in stored)
        self.assertTrue('created' in stored)

    def test_GET_annotation_return_stored_annotation(self):
        example = add_example(self.app)
        response = self.app.get("/api/annotations/annotation/" + example['id'])
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])

    def test_GET_annotations_returns_list_of_annotations(self):
        add_example(self.app)
        response = self.app.get('/api/annotations')
        annotations = get_json(response)
        self.assertTrue(type(annotations) == list)

    def test_PUT_annotation_returns_modified_annotation(self):
        example = add_example(self.app)
        example["motivation"] = "linking"
        response = self.app.put("/api/annotations/annotation/" + example['id'], data=json.dumps(example), content_type="application/json")
        annotation = get_json(response)
        self.assertTrue('modified' in annotation)
        self.assertEqual(annotation['motivation'], example['motivation'])

    def test_DELETE_annotation_returns_removed_annotation(self):
        example = add_example(self.app)
        response = self.app.delete("/api/annotations/annotation/" + example['id'])
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])
        response = self.app.get("/api/annotations/annotation/" + example['id'])
        self.assertEqual(response.status_code, 404)

class TestAnnotationAPIResourceEndpoints(unittest.TestCase):

    def setUp(self):
        annotations_file = make_tempfile()
        server.app.config['DATAFILE'] = annotations_file
        resource_config = {
            "resource_file": make_tempfile(),
            "triple_file": make_tempfile(),
            "url_file": make_tempfile()
        }
        server.resource_store = ResourceStore(resource_config)
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

    def test_api_can_return_registered_resource_map(self):
        self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        response = self.app.get("/api/resources/%s/structure" % (self.letter_map["id"]))
        data = get_json(response)
        self.assertEqual(data["id"], self.letter_map["id"])
        self.assertEqual(data["type"], self.letter_map["type"])
        self.assertEqual(data.keys(), self.letter_map.keys())

    def test_api_can_return_registered_resource_annotations(self):
        self.app.post("/api/resources", data=json.dumps(self.letter_map), content_type="application/json")
        response = self.app.post("/api/annotations", data=json.dumps(self.annotation), content_type="application/json")
        stored_annotation = get_json(response)
        response = self.app.get("/api/resources/%s/annotations" % (self.letter_map["id"]))
        annotations = get_json(response)
        self.assertEqual(annotations[0]["id"], stored_annotation["id"])

if __name__ == "__main__":
    unittest.main()


