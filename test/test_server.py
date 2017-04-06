import unittest
import os
import json
import tempfile
import server as server
from annotation_examples import annotations as examples

def get_json(response):
    return json.loads(response.get_data(as_text=True))

def add_example(app):
    annotation = examples["vincent"]
    response = app.post("/api/annotation", data=json.dumps(annotation), content_type="application/json")
    return get_json(response)

class TestAnnotationAPI(unittest.TestCase):

    def setUp(self):
        _, annotations_file = tempfile.mkstemp()
        server.app.config['DATAFILE'] = annotations_file
        self.app = server.app.test_client()

    def tearDown(self):
        os.unlink(server.app.config['DATAFILE'])

    def test_POST_annotation_returns_annotation_with_id(self):
        annotation = examples["vincent"]
        response = self.app.post("/api/annotation", data=json.dumps(annotation), content_type="application/json")
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


if __name__ == "__main__":
    unittest.main()


