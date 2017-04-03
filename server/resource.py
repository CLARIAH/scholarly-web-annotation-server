from server.vocabulary import VocabularyStore
from rfc3987 import parse as parse_IRI
from collections import defaultdict

class Resource(object):

    def __init__(self, resource_map=None):
        self.validate(resource_map)
        self.resource = resource_map['resource']
        self.typeof = resource_map['typeof']
        self.subresources = {}

    def __repr__(self):
        rv = "%s(%s, %s)\n" % (self.__class__.__name__, self.typeof, self.resource)
        for relation_type in self.get_relations():
            rv += "  %s\n"  % (relation_type)
            for subresource in self.get_subresources(relation_type):
                rv += "    %s(%s, %s)\n" % (subresource.__class__.__name__, subresource.typeof, subresource.resource)
        return rv

    def id(self):
        return self.resource

    def type(self):
        return self.typeof

    def validate(self, resource_map):
        message = None
        if resource_map == None:
            message="Resources should be initialized by a resource map"
        elif type(resource_map) != dict:
            message="Resources MUST be an object with 'resource' and 'typeof' properties"
        elif 'resource' not in resource_map or 'typeof' not in resource_map:
            message="Resource maps MUST have 'resource' and 'typeof' properties"
        if message:
            raise InvalidResourceError(message)

    def add_subresources(self, subresources):
        for relation_type in subresources:
            self.subresources[relation_type] = subresources[relation_type]

    def get_subresources(self, relation_type=None):
        if relation_type == None:
            return self.subresources
        if relation_type not in self.subresources.keys():
            return []
        return self.subresources[relation_type]

    def get_relations(self):
        return self.subresources.keys()

class ResourceStore(object):

    def __init__(self):
        self.required = ["typeof", "vocab", "resource"]
        self.vocab_store = VocabularyStore()
        self.resource_index = {}

    def register_by_map(self, resource_map):
        resource = self.parse_resource(resource_map)
        response = {"ignored": [], "registered": []}
        self.register_resource(resource, response)
        return response

    def register_resource(self, resource, response):
        status = self.index_resource(resource)
        response[status] += [resource.id()]
        for relation_type in resource.get_relations():
            for subresource in resource.get_subresources(relation_type):
                self.register_resource(subresource, response)

    def has_resource(self, resource_id):
        return resource_id in self.resource_index.keys()

    def get_resource(self, resource_id):
        if self.has_resource(resource_id):
            return self.resource_index[resource_id]
        return None

    def get_resource_type(self, resource_id):
        if self.has_resource(resource_id):
            return self.resource_index[resource_id].type()

    def index_resource(self, resource):
        status = "ignored"
        # check if resource is already known
        if resource.id() not in self.resource_index:
            self.resource_index[resource.id()] = resource
            status = "registered"
        registered_type = self.get_resource_type(resource.id())
        if  registered_type != resource.type():
            message = "Conflicting resource types: resource %s is already registered as type %s and cannot be additionally registered as type %s" % (resource.id(), registered_type, resource.type())
            raise InvalidResourceMapError(message)
        return status

    def parse_resource(self, resource_map):
        self.check_required_properties(resource_map)
        self.vocab_store.register_vocabulary(resource_map['vocab'])
        self.check_resource_is_IRI(resource_map["resource"])
        self.check_resource_type_is_valid(resource_map["typeof"])
        subresources = self.get_subresources(resource_map)
        resource = Resource(resource_map)
        resource.add_subresources(subresources)
        return resource

    def check_resource_type_is_valid(self, resource_type):
        resource_class = self.vocab_store.lookupLabel(resource_type)
        if not resource_class or not self.vocab_store.is_class(resource_class):
            message="Illegal resource type: %s" % (resource_type)
            raise InvalidResourceMapError(message)

    def is_relation(self, label, resource_map):
        if label in self.required:
            return False # skip own properties
        subject = self.vocab_store.lookupLabel(label)
        # check if subject belongs to vocabulary specified in resource map
        # TO DO
        # check if subject is relation
        if not subject or not self.vocab_store.is_property(subject):
            message="Illegal resource relationship: %s" % (label)
            raise InvalidResourceMapError(message)
        return True

    def get_subresources(self, resource_map):
        subresources = defaultdict(list)
        for relation_type in self.get_resource_relations(resource_map):
            for subresource_map in resource_map[relation_type]:
                subresource_map['vocab'] = resource_map['vocab']
                subresource = self.parse_resource(subresource_map)
                subresources[relation_type].append(subresource)
        return subresources

    def get_resource_relations(self, resource_map):
        return [key for key in resource_map.keys() if self.is_relation(key, resource_map)]

    def check_required_properties(self, resource_map):
        missing = ", ".join([key for key in self.required if key not in resource_map.keys()])
        if missing:
            message = 'resource is missing the following properties: %s' % (missing)
            raise InvalidResourceMapError(message)

    def check_resource_is_IRI(self, resource_id):
        try:
            parse_IRI(resource_id)
        except ValueError:
            raise InvalidResourceMapError(message = 'resource identifier is not an IRI: %s' % (resource_id))

class InvalidResourceMapError(Exception):
    status_code = 400

    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv

class InvalidResourceError(Exception):
    status_code = 400

    def __init__(self, message, status_code=400, payload=None):
        Exception.__init__(self)
        self.message = message
        self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        rv['status_code'] = self.status_code
        return rv



