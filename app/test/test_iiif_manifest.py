import unittest
import json
import os

from models.iiif_manifest import Manifest
import models.iiif_manifest as iiif


def read_vaint_example():
    vaint_file = "test/vaint_example.json"
    with open(vaint_file, 'rt') as fh:
        json_data = json.load(fh)
        example = {
            'collection': json_data[0],
            'annotation': json_data[1],
        }
        example['annotation']['body'][2] = json_data[2]
        example['annotation']['body'][3] = json_data[3]
        return example


class TestIIIFManifest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\nrunning IIIF Manifest Model tests")

    def setUp(self) -> None:
        self.vaint_example = read_vaint_example()

    def test_check_canvas_items_accepts_empty_list(self):
        self.assertTrue(iiif.check_canvas_items([]))

    def test_web_anno_to_manifest_returns_single_manifest(self):
        manifest = iiif.web_anno_to_manifest(self.vaint_example['annotation'])
        self.assertTrue(isinstance(manifest, Manifest))

    def test_web_anno_to_manifest_returns_manifest(self):
        manifest = iiif.web_anno_to_manifest(self.vaint_example['annotation'])
        self.assertTrue(isinstance(manifest, Manifest))

    def test_manifest_add_canvas_throws_error_if_non_canvas_is_passed(self):
        manifests = iiif.web_anno_to_manifest(self.vaint_example['annotation'])
        error = None
        try:
            manifests.add_canvas_items([1])
        except AssertionError as err:
            error = err
        self.assertNotEqual(error, None)
