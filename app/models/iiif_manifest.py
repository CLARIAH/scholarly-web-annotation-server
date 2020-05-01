import json
from collections import defaultdict
from typing import Dict, List, Union

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
                 items=None, annotations=None):
        if annotations is None:
            annotations = []
        if items is None:
            items = []
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

    def add_annotations(self, page_id: str, annotations: List[Union[Annotation, dict]]):
        """Add a layer of annotations to this canvas in the form of an AnnotationPage. """
        annotation_page = AnnotationPage(page_id, annotations)
        self.annotations += [annotation_page]


class Manifest(object):

    def __init__(self, manifest_uri: Union[str, None] = None, manifest_json: Union[dict, None] = None):
        if manifest_uri:
            self.context = 'http://iiif.io/api/presentation/3/context.json'
            self.type = 'Manifest'
            self.id = manifest_uri
            self.label = ''
            self.metadata = {}
            self.items: List[Canvas] = []
            self.structures = []
            self.annotations: List[AnnotationPage] = []
        elif manifest_json:
            self.context = manifest_json['@context']
            self.id = manifest_json['id']
            self.label = manifest_json['label']
            self.metadata = manifest_json['metadata'] if 'metadata' in manifest_json else {}
            self.items: List[Canvas] = [make_canvas_from_json(canvas_json) for canvas_json in manifest_json['items']]
            self.structures = []
            pages = [AnnotationPage(page_json) for page_json in manifest_json['annotations']]
            self.annotations: List[AnnotationPage] = pages
        else:
            raise ValueError('Cannot make an empty manifest without a manifest URI.')

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


def get_context(json_data: dict) -> Union[None, str]:
    if '@context' in json_data:
        return json_data['@context']
    else:
        return None


def get_type(json_data: dict) -> Union[None, str]:
    if 'type' in json_data:
        return json_data['type']
    else:
        return None


def has_expected_context(json_data: dict) -> None:
    json_context = get_context(json_data)
    expected_context = "http://iiif.io/api/presentation/3/context.json"
    if json_context:
        if isinstance(json_context, list) and expected_context in json_context:
            return None
        if json_data['type'] == expected_context:
            return None
    raise KeyError(f'Manifest MUST have a type property with value "{expected_context}"')


def has_expected_type(json_data: dict, expected_type: str) -> None:
    json_type = get_type(json_data)
    if not json_type:
        raise KeyError(f'{expected_type} MUST have a type property with value "{expected_type}"')
    if isinstance(json_type, list) and expected_type not in json_type:
        raise KeyError(f'{expected_type} MUST have a type property with value "{expected_type}"')
    if json_data['type'] != expected_type:
        raise KeyError(f'{expected_type} MUST have a type property with value "{expected_type}"')


def validate_canvas_json(canvas_json: dict) -> None:
    if not has_expected_type(canvas_json, "Canvas"):
        raise KeyError(f'Canvas MUST have a type property with value Canvas')
    if 'id' not in canvas_json:
        raise KeyError('Canvas MUST have id property')
    height = canvas_json['height'] if 'height' in canvas_json else None
    width = canvas_json['width'] if 'width' in canvas_json else None
    duration = canvas_json['duration'] if 'duration' in canvas_json else None
    if not duration or (not width or not height):
        raise KeyError('Canvas MUST have either "height" and "width" or "duration" or all three properties')
    return None


def make_canvas_from_json(canvas_json: dict) -> Canvas:
    validate_canvas_json(canvas_json)
    height = canvas_json['height'] if 'height' in canvas_json else None
    width = canvas_json['width'] if 'width' in canvas_json else None
    duration = canvas_json['duration'] if 'duration' in canvas_json else None
    items = canvas_json['items'] if 'items' in canvas_json else []
    annotations = canvas_json['annotations'] if 'annotations' in canvas_json else []
    if not duration or (not width or not height):
        raise KeyError('Canvas MUST have either "height" and "width" or "duration" or all three properties')
    canvas = Canvas(canvas_json['id'], height=height, width=width,
                    duration=duration, items=items, annotations=annotations)
    return canvas


def sort_web_annos_by_target(annotations: List[Union[Annotation, dict]]) -> Dict[str, List[Annotation]]:
    manifest_annotations = defaultdict(list)
    for annotation in annotations:
        if isinstance(annotation, dict):
            annotation = Annotation(annotation)
        elif not isinstance(annotation, Annotation):
            raise TypeError('annotations must be of type Annotation of be JSON objects with type property "Annotation"')
        if annotation.motivation == 'painting':
            raise ValueError('Manifest annotations MUST NOT have motivation "painting"')
        target_ids = set(annotation.get_target_ids())
        for target_id in target_ids:
            manifest_annotations[target_id] += [annotation]
    return manifest_annotations


def web_anno_to_manifest(annotations: Union[Annotation, dict, List[Union[Annotation, dict]]]) -> Union[Manifest, List[Manifest]]:
    manifests = []
    if isinstance(annotations, dict) or isinstance(annotations, Annotation):
        annotations = [annotations]
    manifest_annotations = sort_web_annos_by_target(annotations)
    for target_id in manifest_annotations:
        manifest = Manifest(target_id)
        annotation_page_id = manifest.id + '/page/1'
        manifest.add_annotations(annotation_page_id, manifest_annotations[target_id])
        manifests += [manifest]
    if len(manifests) == 1:
        return manifests[0]
    else:
        return manifests


def web_anno_from_manifest(manifest: Union[Manifest, dict]) -> List[Union[Annotation, dict]]:
    """Annotations in a manifest are organised in a list of AnnotationPage elements"""
    annotations = []
    if isinstance(manifest, dict):
        manifest = Manifest(manifest_json=manifest)
    if len(manifest.annotations) == 0:
        return annotations
    for annotation_page in manifest.annotations:
        annotations += [annotation for annotation in annotation_page.items]
    return annotations


