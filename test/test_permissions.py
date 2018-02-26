import unittest
import copy
from annotation_examples import annotations as examples
import models.permissions as permissions
from models.annotation import Annotation
from models.annotation_store import AnnotationStore
#from models.error import *

class TestPermissionModel(unittest.TestCase):

    def setUp(self):
        self.store = AnnotationStore()
        self.example_annotation = copy.copy(examples["vincent"])
        self.params = {
            "access_status": "private",
            "username": "user1"
        }
        self.private_params = {
            "access_status": "private",
            "username": "user1"
        }
        self.public_params = {
            "access_status": "public",
            "username": "user1"
        }
        self.shared_params = {
            "access_status": "shared",
            "username": "user1",
            "can_see": ["user2", "user3"],
            "can_edit": ["user2", "user4"]
        }
        self.anon_params = {
            "access_status": "public",
            "username": None
        }


    def test_anonymous_user_cannot_see_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        self.assertEqual(permissions.is_allowed_to_see(self.anon_params["username"], annotation), False)

    def test_anonymous_user_cannot_see_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        self.assertEqual(permissions.is_allowed_to_see(self.anon_params["username"], annotation), False)

    def test_anonymous_user_can_see_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        self.assertEqual(permissions.is_allowed_to_see(self.anon_params["username"], annotation), True)

    def test_other_user_cannot_see_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_see(params["username"], annotation), False)

    def test_other_user_can_see_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_see(params["username"], annotation), True)

    def test_other_user_can_see_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_see(params["username"], annotation), True)

    def test_owner_user_can_see_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        self.assertEqual(permissions.is_allowed_to_see(self.private_params["username"], annotation), True)

    def test_owner_user_can_see_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        self.assertEqual(permissions.is_allowed_to_see(self.private_params["username"], annotation), True)

    def test_owner_user_can_see_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        self.assertEqual(permissions.is_allowed_to_see(self.private_params["username"], annotation), True)

    def test_anonymous_user_cannot_edit_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.anon_params["username"], annotation), False)

    def test_anonymous_user_cannot_edit_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.anon_params["username"], annotation), False)

    def test_anonymous_user_cannot_edit_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.anon_params["username"], annotation), False)

    def test_other_user_cannot_edit_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_edit(params["username"], annotation), False)

    def test_other_user_can_edit_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_edit(params["username"], annotation), True)

    def test_other_user_who_can_edit_can_also_see_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        params = {"username": "user4"}
        self.assertEqual(permissions.is_allowed_to_edit(params["username"], annotation), True)
        self.assertEqual(permissions.is_allowed_to_see(params["username"], annotation), True)

    def test_other_user_cannot_edit_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        params = {"username": "user2"}
        self.assertEqual(permissions.is_allowed_to_edit(params["username"], annotation), False)

    def test_owner_user_can_edit_private_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.private_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.private_params["username"], annotation), True)

    def test_owner_user_can_edit_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.shared_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.shared_params["username"], annotation), True)

    def test_owner_user_can_edit_public_annotation(self):
        annotation = Annotation(self.example_annotation)
        permissions.add_permissions(annotation, self.public_params)
        self.assertEqual(permissions.is_allowed_to_edit(self.private_params["username"], annotation), True)

    def test_can_see_user_cannot_edit_shared_annotation(self):
        annotation = Annotation(self.example_annotation)
        params = {
            "access_status": "shared",
            "username": "user1",
            "can_see": ["user2", "user3"],
            "can_edit": ["user4"]
        }
        permissions.add_permissions(annotation, params)
        self.assertEqual(permissions.is_allowed_action(params["can_see"][0], "see", annotation), True)
        self.assertEqual(permissions.is_allowed_action(params["can_see"][0], "edit", annotation), False)


if __name__ == "__main__":
    unittest.main()


