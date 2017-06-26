import urllib
import math
import copy
from models.annotation import Annotation, AnnotationError
from models.annotation_collection import AnnotationCollection

class AnnotationContainer(object):

    def __init__(self, base_url, data, page_size=100, view="PreferMinimalContainer"):
        self.base_url = base_url
        self.context = ["http://www.w3.org/ns/ldp.jsonld", "http://www.w3.org/ns/anno.jsonld"]
        self.set_view(view)
        self.set_page_size(page_size)
        self.set_container_content(data)
        if self.metadata["total"] > 0:
            self.first = self.update_url(self.base_url, {"page": 0})
            self.last = self.update_url(self.base_url, {"page": self.num_pages - 1})

    def generate_metadata_from_collection(self, collection):
        self.metadata = {
            "@context": self.context,
            "id": self.base_url,
            "creator": collection["creator"],
            "created": collection["created"],
            "label": collection["label"],
            "total": collection["total"],
            "type": ["BasicContainer", collection["type"]]
        }
        self.num_pages = int(math.ceil(collection["total"] / self.page_size))
        if "modified" in collection:
            self.metadata["modified"] = collection["modified"]

    def generate_metadata_from_annotations(self, annotations):
        self.metadata = {
            "@context": self.context,
            "id": self.base_url,
            "total": len(annotations),
            "type": ["BasicContainer", "AnnotationContainer"]
        }
        self.num_pages = int(math.ceil(len(annotations) / self.page_size))

    def set_view(self, view):
        if view == "PreferMinimalContainer":
            self.view = self.viewMinimalContainer
            self.iris=1
        elif view == "PreferContainedIRIs":
            self.view = self.viewContainedIRIs
            self.iris=1
        elif view == "PreferContainedDescriptions":
            self.view = self.viewContainedDescriptions
            self.iris=0
        else:
            raise AnnotationError(message="%s is not a valid container option. Value MUST be one of PreferMinimalContainer, PreferContainedIRIs, PreferContainedDescriptions" % (view))
        self.base_url = self.update_url(self.base_url, {"iris": self.iris})

    def viewMinimalContainer(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = self.first
            self.metadata["last"] = self.last
        return self.metadata

    def viewContainedIRIs(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = {
                "id": self.update_url(self.base_url, {"page": 0}),
                "type": "AnnotationPage",
                "items": self.add_page_items(0)
            }
            self.add_page_refs(self.metadata["first"], 0)
            self.metadata["last"] = self.last
        return self.metadata

    def viewContainedDescriptions(self):
        if self.metadata["total"] > 0:
            self.metadata["first"] = {
                "id": self.update_url(self.base_url, {"page": 0}),
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
            "id": self.update_url(self.base_url, {"page": page_num}),
            "type": "AnnotationPage",
            "partOf": self.add_collection_ref(),
            "startIndex": self.page_size * page_num,
            "items": self.add_page_items(page_num)
        }
        self.add_page_refs(page_metadata, page_num)
        return page_metadata

    def add_page_refs(self, page_metadata, page_num):
        if page_num > 0:
            page_metadata["prev"] = self.update_url(self.base_url, {"page": page_num-1})
        if page_num < self.num_pages - 1:
            page_metadata["next"] = self.update_url(self.base_url, {"page": page_num+1})

    def add_collection_ref(self):
        partOf = {
            "id": self.base_url,
            "total": self.metadata["total"],
        }
        if "modified" in self.metadata:
            partOf["modified"] = self.modified
        return partOf

    def add_page_items(self, page_num):
        startIndex = self.page_size * page_num
        items = self.items[startIndex: startIndex + self.page_size]
        if self.iris:
            return [item.id for item in items]
        else:
            return [item.data for item in items]

    def set_container_content(self, data):
        if isinstance(data, AnnotationCollection):
            self.items = data.items
            self.generate_metadata_from_collection(data.to_json())
        elif self.is_annotation_list(data):
            self.items = data
            self.generate_metadata_from_annotations(data)
        else:
            raise AnnotationError(message="data should be an AnnotationCollection or a list of Annotations")

    def set_page_size(self, page_size):
        if type(page_size) != int or page_size < 1:
            raise AnnotationError(message='page_size must be a positive integer value')
        self.page_size = page_size

    def is_annotation_list(self, annotations):
        if not isinstance(annotations, list):
            return False
        for annotation in annotations:
            if not isinstance(annotation, Annotation):
                return False
        return True

    def update_url(self, base_url, params):
        # This function is taken from:
        # https://gist.github.com/rokcarl/20b5bf8dd9b1998880b7
        # resulting on the following discussions
        # https://stackoverflow.com/questions/2506379/add-params-to-given-url-in-python
        url_parts = list(urllib.parse.urlparse(base_url))
        query = dict(urllib.parse.parse_qsl(url_parts[4]))
        query.update(params)
        url_parts[4] = urllib.parse.urlencode(query)
        return urllib.parse.urlunparse(url_parts)

