import unittest
import base64
import copy
import os
import json
from elasticsearch import Elasticsearch
import annotation_server as server
from annotation_examples import annotations as examples, annotation_collections as example_collections
from models.annotation_store import AnnotationStore
from models.user_store import UserStore
from models.user import User

config = {
    "host": "localhost",
    "port": 9200,
    "annotation_index": "unittest-test-annotation-index",
    "user_index": "unittest-test-user-index",
    "page_size": 1000,
    "user1": {
        "username": "user1",
        "password": "pass1"
    },
    "user2": {
        "username": "user2",
        "password": "pass2"
    }
}

def get_json(response):
    return json.loads(response.get_data(as_text=True))

def seed_user_index():
    es = Elasticsearch([{"host": config['host'], "port": config['port']}])
    user = User({"username": config["user1"]["username"]})
    user.hash_password(config["user1"]["password"])
    es.index(index=config["user_index"], doc_type="user", id=user.username, body=user.json())
    es.indices.refresh(index=config["user_index"])

def remove_test_indexes():
    es = Elasticsearch([{"host": config['host'], "port": config['port']}])
    if es.indices.exists(index=config["user_index"]):
        es.indices.delete(index=config["user_index"])
    if es.indices.exists(index=config["annotation_index"]):
        es.indices.delete(index=config["annotation_index"])

class TestAnnotationAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nrunning Annotation API tests")
        seed_user_index()

    def setUp(self):
        server.annotation_store = AnnotationStore() # always start with empty store
        server.annotation_store.configure_index(config)
        server.user_store = UserStore(configuration=config)
        self.app = server.app.test_client()
        self.headers1 = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(config["user1"]["username"] + ":" + config["user1"]["password"], 'ascii')).decode('ascii')
        }
        self.headers2 = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(config["user2"]["username"] + ":" + config["user2"]["password"], 'ascii')).decode('ascii')
        }

    def tearDown(self):
        # make sure to remove temp index
        server.annotation_store.es.indices.delete(config["annotation_index"])
        #server.user_store.es.indices.delete(config["user_index"])

    def register_user(self):
        return self.app.post("/api/users", data=json.dumps({"username": self.testuser, "password": self.testpass}), content_type="application/json")

    def add_example(self, access_status=None):
        annotation = copy.copy(examples["vincent"])
        if access_status:
            url_params = {"access_status": access_status}
            response = self.app.post("/api/annotations", query_string=url_params, data=json.dumps(annotation), content_type="application/json", headers=self.headers1)
        else:
            response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json", headers=self.headers1)
        return get_json(response)

    def test_POST_invalid_annotation_unauthorized_returns_an_unauthorized_error(self):
        annotation = copy.copy(examples["no_target"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_POST_annotation_unauthorized_returns_an_error(self):
        annotation = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_POST_annotation_returns_annotation_with_id(self):
        annotation = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json", headers=self.headers1)
        self.assertEqual(response.status_code, 201)
        stored = get_json(response)
        self.assertTrue('id' in stored)
        self.assertTrue('created' in stored)

    def test_anonymous_GET_annotation_returns_public_annotation(self):
        example = self.add_example(access_status="public")
        response = self.app.get("/api/annotations/" + example['id'])
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])

    def test_anonymous_GET_annotation_returns_no_private_annotations(self):
        example = self.add_example(access_status="private")
        response = self.app.get("/api/annotations/" + example['id'])
        self.assertEqual(response.status_code, 403)

    def test_authorized_GET_annotation_returns_stored_annotation(self):
        example = self.add_example(access_status="private")
        response = self.app.get("/api/annotations/" + example['id'], headers=self.headers1)
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])

    def test_authorized_GET_annotation_returns_stored_annotation_without_permission_info(self):
        example = self.add_example(access_status="private")
        response = self.app.get("/api/annotations/" + example['id'], headers=self.headers1)
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])
        self.assertEqual("permissions" in annotation, False)

    def test_authorized_GET_annotation_returns_stored_annotation(self):
        example = self.add_example(access_status="private")
        url_params = {"include_permissions": "true"}
        response = self.app.get("/api/annotations/" + example['id'], query_string=url_params, headers=self.headers1)
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])
        self.assertEqual(annotation["permissions"]["owner"], config["user1"]["username"])

    def test_unauthorized_GET_annotation_returns_error(self):
        example = self.add_example(access_status="private")
        response = self.app.get("/api/annotations/" + example['id'], headers=self.headers2)
        self.assertEqual(response.status_code, 403)

    def test_GET_annotations_returns_annotation_container(self):
        headers = copy.copy(self.headers1)
        headers["Prefer"] = 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedDescriptions"'
        self.add_example(access_status="private")
        server.annotation_store.es.indices.refresh(config["annotation_index"])
        response = self.app.get('/api/annotations', headers=headers)
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(container["total"], 1)

    def test_GET_annotations_with_descriptions_returns_container_with_descriptions(self):
        self.add_example(access_status = "private")
        server.annotation_store.es.indices.refresh(config["annotation_index"])
        headers = copy.copy(self.headers1)
        headers["Prefer"] = 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedDescriptions"'
        response = self.app.get('/api/annotations', headers=headers)
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(len(container["first"]["items"]), 1)
        self.assertEqual(container["total"], 1)

    def test_GET_annotations_by_unknown_target_via_query_returns_empty_container(self):
        headers = copy.copy(self.headers1)
        headers["Prefer"] = 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedDescriptions"'
        target_id = examples["vincent"]["target"][0]["id"]
        url_params = {"target_id": examples["vincent"]["target"][0]["id"]}
        response = self.app.get('/api/annotations', query_string=url_params, headers=headers)
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(container["total"], 0)

    def test_GET_annotations_by_target_via_query_returns_container(self):
        headers = copy.copy(self.headers1)
        headers["Prefer"] = 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedDescriptions"'
        annotation1 = self.add_example(access_status="private")
        annotation2 = copy.copy(examples["theo"]) # second example, different target
        response = self.app.post("/api/annotations", data=json.dumps(annotation2), content_type="application/json", headers=self.headers1)
        url_params = {"target_id": annotation1["target"][0]["id"]}
        server.annotation_store.es.indices.refresh(config["annotation_index"])
        response = self.app.get('/api/annotations', query_string=url_params, headers=headers)
        container = get_json(response)
        self.assertTrue("AnnotationContainer" in container["type"])
        self.assertEqual(container["total"], 1)
        self.assertEqual(container["first"]["items"][0]["target"][0]["id"], annotation1["target"][0]["id"])

    def test_PUT_annotation_returns_modified_annotation(self):
        example = self.add_example()
        example["motivation"] = "linking"
        response = self.app.put("/api/annotations/" + example['id'], data=json.dumps(example), content_type="application/json", headers=self.headers1)
        annotation = get_json(response)
        self.assertTrue('modified' in annotation)
        self.assertEqual(annotation['motivation'], example['motivation'])

    def test_DELETE_annotation_returns_removed_annotation(self):
        example = self.add_example()
        response = self.app.delete("/api/annotations/" + example['id'], headers=self.headers1)
        annotation = get_json(response)
        self.assertEqual(annotation['id'], example['id'])
        response = self.app.get("/api/annotations/" + example['id'], headers=self.headers1)
        self.assertEqual(response.status_code, 404)

class TestAnnotationAPICollectionEndpoints(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nrunning AnnotationCollection API tests")
        server.user_store = UserStore(configuration=config)
        seed_user_index()

    def setUp(self):
        server.annotation_store = AnnotationStore() # always start with empty store
        server.annotation_store.configure_index(config)
        self.app = server.app.test_client()
        self.headers1 = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(config["user1"]["username"] + ":" + config["user1"]["password"], 'ascii')).decode('ascii')
        }
        self.headers2 = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(config["user2"]["username"] + ":" + config["user2"]["password"], 'ascii')).decode('ascii')
        }
        #self.register_user()

    def register_user(self):
        return self.app.post("/api/users", data=json.dumps({"username": self.testuser, "password": self.testpass}), content_type="application/json")


    def tearDown(self):
        server.annotation_store.es.indices.delete(config["annotation_index"])

    def add_example(self, access_status=None):
        collection_raw = example_collections["empty_collection"]
        if access_status:
            url_params = {"access_status": access_status}
            response = self.app.post("/api/collections", query_string=url_params, data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        else:
            response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        return get_json(response)

    def test_api_cannot_create_collection_by_anonymous_user(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_api_cannot_create_collection_by_unauthorized_user(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers2)
        self.assertEqual(response.status_code, 403)

    def test_api_can_create_collection_by_authorized_user(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        self.assertEqual(response.status_code, 201)
        self.assertTrue("id" in collection_registered)
        self.assertEqual(collection_registered["label"], collection_raw["label"])
        self.assertEqual(collection_registered["creator"], collection_raw["creator"])

    def test_api_can_retrieve_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]), headers=self.headers1)
        collection_retrieved = get_json(response)
        self.assertEqual(response.status_code, 200)
        for key in collection_retrieved.keys():
            self.assertEqual(collection_retrieved[key], collection_registered[key])

    def test_api_can_update_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        collection_registered["label"] = "New label"
        response = self.app.put("/api/collections/%s" % (collection_registered["id"]), data=json.dumps(collection_registered), content_type="application/json", headers=self.headers1)
        collection_updated = get_json(response)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(collection_updated["label"], collection_registered["label"])
        self.assertTrue("modified" in collection_updated)

    def test_api_can_delete_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        response = self.app.delete("/api/collections/%s" % (collection_registered["id"]), headers=self.headers1)
        collection_deleted = get_json(response)
        self.assertEqual(collection_registered["id"], collection_deleted["id"])
        self.assertEqual(collection_deleted["status"], "deleted")
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]))
        self.assertEqual(response.status_code, 404)

    def test_api_can_add_annotation_to_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        self.assertEqual(collection_registered["total"], 0)
        annotation_raw = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation_raw), content_type="application/json", headers=self.headers1)
        annotation_registered = get_json(response)
        headers = copy.copy(self.headers1)
        headers["Prefer"] = 'return=representation;include="http://www.w3.org/ns/oa#PreferContainedIRIs"'
        response = self.app.post("/api/collections/%s/annotations/" % (collection_registered["id"]), data=json.dumps(annotation_registered), content_type="application/json", headers=self.headers1)
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]), headers=headers)
        collection_retrieved = get_json(response)
        self.assertEqual(collection_retrieved["total"], 1)
        self.assertEqual(collection_retrieved["first"]["items"][0], annotation_registered["id"])

    def test_api_can_remove_annotation_from_collection(self):
        collection_raw = example_collections["empty_collection"]
        response = self.app.post("/api/collections", data=json.dumps(collection_raw), content_type="application/json", headers=self.headers1)
        collection_registered = get_json(response)
        self.assertEqual(collection_registered["total"], 0)
        annotation_raw = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation_raw), content_type="application/json", headers=self.headers1)
        annotation_registered = get_json(response)
        self.app.post("/api/collections/%s/annotations/" % (collection_registered["id"]), data=json.dumps(annotation_registered), content_type="application/json", headers=self.headers1)
        response = self.app.delete("/api/collections/%s/annotations/%s" % (collection_registered["id"], annotation_registered["id"]), headers=self.headers1)
        response = self.app.get("/api/collections/%s" % (collection_registered["id"]), headers=self.headers1)
        collection_retrieved = get_json(response)
        self.assertEqual(collection_retrieved["total"], 0)

class TestUserAPI(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nrunning User API tests")

    def setUp(self):
        self.remove_test_index() # make sure there is no previous test index
        server.user_store = UserStore(configuration=config)
        self.app = server.app.test_client()
        self.testuser = "testuser"
        self.testpass = "testpass"
        self.headers = {
            'Authorization': 'Basic ' + base64.b64encode(bytes(self.testuser + ":" + self.testpass, 'ascii')).decode('ascii')
        }
        self.unauthorized_headers = {
            'Authorization': 'Basic ' + base64.b64encode(bytes("unknown" + ":" + "unknown", 'ascii')).decode('ascii')
        }

    def create_headers(self, username, password):
        return {
            'Authorization': 'Basic ' + base64.b64encode(bytes(username + ":" + password, 'ascii')).decode('ascii')
        }

    def remove_test_index(self):
        es = Elasticsearch([{"host": config['host'], "port": config['port']}])
        if es.indices.exists(index=config["user_index"]):
            es.indices.delete(index=config["user_index"])

    def tearDown(self):
        self.remove_test_index() # make sure to remove test index

    def register_user(self):
        return self.app.post("/api/users", data=json.dumps({"username": self.testuser, "password": self.testpass}), content_type="application/json")

    def test_POST_user_without_password_returns_an_error(self):
        response = self.app.post("/api/users", data=json.dumps({"username": self.testuser}), content_type="application/json")
        self.assertEqual(response.status_code, 400)

    def test_POST_user_with_password_returns_user_created(self):
        response = self.app.post("/api/users", data=json.dumps({"username": self.testuser, "password": self.testpass}), content_type="application/json")
        response_data = get_json(response)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_data["action"], "created")

    def test_POST_login_without_password_returns_error(self):
        response = self.app.post("/api/login", data=json.dumps({"username": self.testuser}), content_type="application/json")
        self.assertEqual(response.status_code, 403)

    def test_POST_login_with_unregistered_user_returns_error(self):
        response = self.app.post("/api/login", content_type="application/json", headers=self.unauthorized_headers)
        self.assertEqual(response.status_code, 403)

    def test_POST_login_with_password_returns_verified(self):
        self.register_user()
        response = self.app.post("/api/login", content_type="application/json", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response_data = get_json(response)
        self.assertEqual(response_data["action"], "verified")

    def test_POST_authorized_login_returns_a_token(self):
        self.register_user()
        response = self.app.post("/api/login", content_type="application/json", headers=self.headers)
        self.assertEqual(response.status_code, 200)
        response_data = get_json(response)
        self.assertEqual("token" in response_data["user"].keys(), True)

    def test_POST_private_annotation_with_authorization_token_returns_annotation_created(self):
        self.register_user()
        response = self.app.post("/api/login", content_type="application/json", headers=self.headers)
        data = get_json(response)
        headers = self.create_headers(data["user"]["token"], "unused")
        annotation = copy.copy(examples["vincent"])
        response = self.app.post("/api/annotations", data=json.dumps(annotation), content_type="application/json", headers=headers)
        self.assertEqual(response.status_code, 201)

    def test_PUT_user_without_old_password_returns_error(self):
        self.register_user()
        response = self.app.put("/api/users", data=json.dumps({"password": "new_pass"}), content_type="application/json", headers=self.headers)
        self.assertEqual(response.status_code, 400)

    def test_PUT_unregistered_user_returns_error(self):
        headers = {
            'Authorization': 'Basic ' + base64.b64encode(bytes("unknown" + ":" + self.testpass, 'ascii')).decode('ascii')
        }
        response = self.app.put("/api/users", data=json.dumps({"username": "unknown", "password": "new_pass"}), content_type="application/json", headers=headers)
        self.assertEqual(response.status_code, 403)

    def test_PUT_user_with_old_and_new_password_returns_password_updated(self):
        self.register_user()
        response = self.app.put("/api/users", data=json.dumps({"password": self.testpass, "new_password": "new_pass"}), content_type="application/json", headers=self.headers)
        response_data = get_json(response)
        self.assertEqual(response_data["action"], "updated")

    def test_DELETE_login_with_password_returns_verified(self):
        self.register_user()
        response = self.app.delete("/api/users", data=json.dumps({"username": self.testuser, "password": self.testpass}), content_type="application/json", headers=self.headers)
        self.assertEqual(response.status_code, 204)


if __name__ == "__main__":
    pass
    #unittest.main()


