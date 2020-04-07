from urllib import parse as url_parser
import math
import copy
import json
from typing import List, Union
from rfc3987 import parse as parse_iri

from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection


def is_annotation_list(annotations):
    if not isinstance(annotations, list):
        return False
    for annotation in annotations:
        try:
            # copy to make sure annotation is not changed
            Annotation(copy.copy(annotation))
        except AnnotationError:
            return False
    return True


def is_annotation_collection(data):
    if not isinstance(data, dict):
        return False
    if isinstance(data["type"], str) and data["type"] == "AnnotationCollection":
        return True
    elif isinstance(data["type"], list) and "AnnotationCollection" in data["type"]:
        return True
    else:
        return False


def is_annotation(data):
    if isinstance(data, Annotation):
        return True
    elif not isinstance(data, dict or "type" not in data):
        return False
    elif isinstance(data["type"], str) and data["type"] == "Annotation":
        return True
    elif isinstance(data["type"], list) and "Annotation" in data["type"]:
        return True
    else:
        return False


def update_url(base_url, params):
    # This function is taken from:
    # https://gist.github.com/rokcarl/20b5bf8dd9b1998880b7
    # mentioned in the following discussions
    # https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python
    url_parts = list(url_parser.urlparse(base_url))
    query = dict(url_parser.parse_qsl(url_parts[4]))
    query.update(params)
    url_parts[4] = url_parser.urlencode(query)
    return url_parser.urlunparse(url_parts)


class AnnotationContainer(object):

    def __init__(self, base_url, data, page_size=100, view="PreferMinimalContainer", total=None):
        self.base_url = base_url
        self.context = ["http://www.w3.org/ns/ldp.jsonld", "http://www.w3.org/ns/anno.jsonld"]
        self.metadata = {}
        self.num_pages = 0
        self.view = {}
        self.iris = 1
        self.modified = None
        self.items = None
        self.page_size = 0
        self.set_view(view)
        self.set_page_size(page_size)
        self.set_container_content(data, total)
        if self.metadata["total"] > 0:
            self.first = update_url(self.base_url, {"page": 0})
            self.last = update_url(self.base_url, {"page": self.num_pages - 1})

    def generate_metadata_from_collection(self, collection):
        self.metadata = {
            "@context": self.context,
            "id": collection["id"],
            "creator": collection["creator"],
            "created": collection["created"],
            "label": collection["label"],
            "total": collection["total"],
            "type": ["BasicContainer", collection["type"]]
        }
        self.num_pages = int(math.ceil(collection["total"] / self.page_size))
        if "modified" in collection:
            self.metadata["modified"] = collection["modified"]

    def generate_metadata_from_annotations(self, annotations, total):
        if total is None:
            total = len(annotations)
        self.metadata = {
            "@context": self.context,
            "id": self.base_url,
            "total": total,
            "type": ["BasicContainer", "AnnotationContainer"]
        }
        self.num_pages = int(math.ceil(len(annotations) / self.page_size))

    def set_view(self, view):
        if view == "PreferMinimalContainer":
            self.view = self.view_minimal_container
            self.iris = 1
        elif view == "PreferContainedIRIs":
            self.view = self.view_contained_iris
            self.iris = 1
        elif view == "PreferContainedDescriptions":
            self.view = self.view_contained_descriptions
            self.iris = 0
        else:
            raise AnnotationError(message="%s is not a valid container option. Value MUST be one of "
                                          "PreferMinimalContainer, PreferContainedIRIs, PreferContainedDescriptions"
                                          % view)
        self.base_url = update_url(self.base_url, {"iris": self.iris})

    def view_minimal_container(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = self.first
            self.metadata["last"] = self.last
        return self.metadata

    def view_contained_iris(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = {
                "id": update_url(self.base_url, {"page": 0}),
                "type": "AnnotationPage",
                "items": self.add_page_items(0)
            }
            self.add_page_refs(self.metadata["first"], 0)
            self.metadata["last"] = self.last
        return self.metadata

    def view_contained_descriptions(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = {
                "id": update_url(self.base_url, {"page": 0}),
                "type": "AnnotationPage",
                "items": self.add_page_items(0)
            }
            self.add_page_refs(self.metadata["first"], 0)
            self.metadata["last"] = self.last
        return self.metadata

    def view_page(self, page=0):
        if not isinstance(page, int) or page < 0:
            raise AnnotationError(message="Parameter page must be non-negative integer")
        return self.generate_page_metadata(page)

    def generate_page_metadata(self, page_num):
        page_metadata = {
            "@context": "http://www.w3.org/ns/anno.jsonld",
            "id": update_url(self.base_url, {"page": page_num}),
            "type": "AnnotationPage",
            "partOf": self.add_collection_ref(),
            "startIndex": self.page_size * page_num,
            "items": self.add_page_items(page_num)
        }
        self.add_page_refs(page_metadata, page_num)
        return page_metadata

    def add_page_refs(self, page_metadata, page_num):
        if page_num > 0:
            page_metadata["prev"] = update_url(self.base_url, {"page": page_num-1})
        if page_num < self.num_pages - 1:
            page_metadata["next"] = update_url(self.base_url, {"page": page_num+1})

    def add_collection_ref(self):
        part_of = {
            "id": self.base_url,
            "total": self.metadata["total"],
        }
        if "modified" in self.metadata:
            part_of["modified"] = self.metadata['modified']
        return part_of

    def add_page_items(self, page_num):
        start_index = self.page_size * page_num
        items = self.items[start_index: start_index + self.page_size]
        if self.iris:
            if isinstance(items[0], str):
                return items
            else:
                return [item["id"] for item in items]
        else:
            return [item for item in items]

    def set_container_content(self, data, total):
        data_json = self.make_json(data)
        if is_annotation_collection(data_json):
            self.items = data_json["items"]
            self.generate_metadata_from_collection(data_json)
        elif is_annotation_list(data_json):
            self.items = data_json
            self.generate_metadata_from_annotations(data_json, total)
        else:
            raise AnnotationError(message="data should be an AnnotationCollection or a list of Annotations")

    def set_page_size(self, page_size):
        if type(page_size) != int or page_size < 1:
            raise AnnotationError(message='page_size must be a positive integer value')
        self.page_size = page_size

    def make_json(self, data):
        if isinstance(data, AnnotationCollection):
            return data.to_json()
        if isinstance(data, Annotation):
            return data.data
        elif isinstance(data, list):
            return [self.make_json(item) for item in data]
        elif isinstance(data, dict) and "type" in data:
            return data
        else:
            raise AnnotationError(message="data should be an AnnotationCollection or a list of Annotations")


class AnnotationPage(object):

    def __init__(self, page_id: str, items: Union[None, List[Union[Annotation, dict]]] = None):
        self.type = 'AnnotationPage'
        if not parse_iri(page_id, rule="IRI"):
            raise ValueError('AnnotationPage id MUST be an IRI')
        self.id = page_id
        if items:
            for item in items:
                if isinstance(item, Annotation):
                    pass
                elif isinstance(item, dict) and 'type' in item and item['type'] == 'Annotation':
                    pass
                else:
                    raise TypeError('items must be of type Annotation or JSON objects with type "Annotation"')
        # ensure all annotations are validated and added as annotation objects
        items = [Annotation(annotation) if isinstance(annotation, dict) else annotation for annotation in items]
        self.items: List[Annotation] = items if items else []
        # if this page is not the last in the collection, it must have 'next' property
        self.next = None
        # if page is partOf collection is *should* have 'partOf' property
        self.part_of = None
        # page *should* have a 'startIndex', *must* not have more than one
        self.start_index = None
        # if page is not the first in the collection, it *should* have a 'prev' property
        self.prev = None

    def __repr__(self):
        return self.to_json()

    def __str__(self):
        return json.dumps(self.__repr__(), indent=2)

    def to_json(self):
        json_data = {
            'type': self.type,
            'id': self.id,
            'items': [annotation.to_json() for annotation in self.items],
        }
        if self.next:
            json_data['next'] = self.next
        if self.prev:
            json_data['prev'] = self.prev
        if self.start_index:
            json_data['startIndex'] = self.start_index
        if self.part_of:
            json_data['partOf'] = self.part_of
        return json_data
