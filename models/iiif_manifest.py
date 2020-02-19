import json
from typing import List, Dict, Union
from models.annotation import Annotation
from models.annotation_container import AnnotationPage


def check_canvas_items(canvas_items: List[dict]):
    for canvas_item in canvas_items:
        if 'type' not in canvas_item or canvas_item['type'] is not 'AnnotationPage':
            raise ValueError('Canvas items MUST be of type AnnotationPage.')
        for annotation in canvas_item['items']:
            if 'motivation' not in annotation:
                annotation['motivation'] = 'painting'
            elif annotation['motivation'] != 'painting':
                raise ValueError('Canvas annotations must have motivation "painting"')
    return True


class Canvas(object):

    # Every Canvas should have a label to display. If one is not provided,
    # the client should automatically generate one for use based on the
    # Canvas’s position within the items property.
    def __init__(self, canvas_uri: str, height: Union[int, None], width: Union[int, None],
                 duration: Union[int, float, None] = None,
                 items: List[dict] = [], annotations: List[dict] = []):
        self.id = canvas_uri
        self.type = 'Canvas'
        self.label = ''
        if (not height or not width) and not duration:
            raise ValueError('Canvas MUST have either "height" and "width" or "duration" or both')
        self.height = height
        self.width = width
        self.duration = duration
        check_canvas_items(items)
        self.items = items
        self.annotations = annotations

    def to_json(self):
        canvas_json = {
            'id': self.id,
            'type': self.type,
            'label': self.label,
            'items': self.items,
        }
        if self.height and self.width:
            canvas_json['height'] = self.height
            canvas_json['width'] = self.width
        if self.duration:
            canvas_json['duration'] = self.duration
        if len(self.annotations) > 0:
            canvas_json['annotations'] = self.annotations
        return canvas_json


class Manifest(object):

    def __init__(self, manifest_uri: str):
        self.context = 'http://iiif.io/api/presentation/3/context.json'
        self.type = 'Manifest'
        self.id = manifest_uri
        self.label = ''
        # metadata
        self.metadata = {}
        self.items: List[Canvas] = []
        self.structures = []
        self.annotations: List[AnnotationPage] = []

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return json.dumps(self.__repr__(), indent=2)

    def add_canvas_items(self, items: List[Canvas]):
        for item in items:
            assert(isinstance(item, Canvas))
        self.items = items

    def to_json(self):
        manifest_json = {
            '@context': self.context,
            'type': self.type,
            'id': self.id,
            'label': self.label,
            'items': [canvas.to_json() for canvas in self.items]
        }
        if len(self.metadata.keys()) > 0:
            manifest_json['metadata'] = self.metadata
        if len(self.structures) > 0:
            manifest_json['structures'] = self.structures
        if len(self.annotations) > 0:
            manifest_json['annotations'] = [annotation_page.to_json() for annotation_page in self.annotations]
        return manifest_json

    def add_annotations(self, page_id: str, annotations: List[Union[Annotation, dict]]):
        """Add a layer of annotations to this canvas in the form of an AnnotationPage. """
        annotation_page = AnnotationPage(page_id, annotations)
        self.annotations += [annotation_page]


def web_anno_to_manifest(annotation: dict) -> List[Manifest]:
    manifests = []
    if isinstance(annotation['target'], list):
        for target in annotation['target']:
            if 'id' in target:
                manifest = Manifest(target['id'])
                manifests += [manifest]
    elif isinstance(annotation['target'], object):
        manifest = Manifest(annotation['target']['id'])
        annotation_page_id = manifest.id + '/page/1'
        manifest.add_annotations(annotation_page_id, [annotation])
        manifests += [manifest]
    return manifests



