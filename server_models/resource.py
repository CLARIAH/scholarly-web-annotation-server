import pickle
import datetime
import pytz
import uuid
from server_models.vocabulary import VocabularyStore
from rfc3987 import parse as parse_IRI
from collections import defaultdict

class Resource(object):

    def __init__(self, resource_map=None):
        self.validate(resource_map)
        self.id = resource_map["id"]
        self.type = resource_map["type"]
        self.vocab = resource_map["vocab"]
        self.subresources = defaultdict(list)
        self.created = datetime.datetime.now(pytz.utc).isoformat()
        self.uuid = uuid.uuid4().urn

    def __repr__(self):
        rv = "%s(%s, %s)\n" % (self.__class__.__name__, self.type, self.id)
        rv += "@context: %s\n" % (self.vocab)
        for relation_type in self.get_relations():
            rv += "  %s\n"  % (relation_type)
            for subresource in self.get_subresources(relation_type):
                rv += "    %s(%s, %s)\n" % (subresource.__class__.__name__, subresource.type, subresource.id)
        return rv

    def json(self):
        return {
            "id": self.id,
            "type": self.type,
            "vocabulary": self.vocab,
            "registered": [
                {
                    "timestamp": self.created,
                    "agent": "TO-DO",
                    "source_location": "TO-DO"
                },
            ],
            "uuid": self.uuid
        }

    def validate(self, resource_map):
        required = ["id", "type", "vocab"]
        message = None
        if resource_map == None:
            message="Resources should be initialized by a resource map"
            raise ResourceError(message)
        elif type(resource_map) != dict:
            message="Resources MUST be an object with 'id', 'type' and 'vocab' properties"
            raise ResourceError(message)
        for property in required:
            if property not in resource_map.keys():
                message="Resource maps MUST have 'id' and 'type' properties"
                raise ResourceError(message)

    def add_subresources(self, subresources, relation_type=None):
        if relation_type:
            for subresource in subresources[relation_type]:
                self.add_subresource(subresource, relation_type)
        for relation_type in subresources.keys():
            for subresource in subresources[relation_type]:
                self.add_subresource(subresource, relation_type)

    def add_subresource(self, subresource, relation_type):
        if isinstance(subresource, Resource):
            self.subresources[relation_type] += [subresource]
        else:
            raise(ResourceError(message="subresource is not a Resource object"))

    def get_subresources(self, relation_type=None):
        if relation_type == None:
            return self.subresources
        if relation_type not in self.subresources.keys():
            return []
        return self.subresources[relation_type]

    def get_relations(self):
        return self.subresources.keys()

    def list_members(self, requested_type=None):
        members = []
        if not requested_type or self.type == requested_type:
            members += [self.id]
        for relation_type in self.subresources.keys():
            if requested_type and relation_type != requested_type:
                continue
            for subresource in self.subresources[relation_type]:
                members += subresource.list_members(requested_type)
        return members

class ResourceStore(object):

    def __init__(self, config):
        self.resource_file = config['resource_file']
        self.required = ["type", "vocab", "id"]
        self.vocab_store = VocabularyStore(config)
        self.resource_index = {}
        self.load_index()

    def has_resource(self, resource_id):
        return resource_id in self.resource_index.keys()

    def get_resource(self, resource_id):
        if self.has_resource(resource_id):
            return self.resource_index[resource_id]
        return None

    def get_resource_type(self, resource_id):
        if self.has_resource(resource_id):
            return self.resource_index[resource_id].type

    def register_by_map(self, resource_map):
        resource = self.parse_resource_map(resource_map)
        response = {"ignored": [], "registered": []}
        self.register_resource(resource, response)
        return response

    def register_resource(self, resource, response):
        status = self.index_resource(resource)
        response[status] += [resource.id]
        for relation_type in resource.get_relations():
            for subresource in resource.get_subresources(relation_type):
                self.register_resource(subresource, response)

    def index_resource(self, resource):
        # check if resource is already known
        if self.has_resource(resource.id):
            self.check_type_consistent(resource.id, resource.type)
            return "ignored"
        else:
            self.resource_index[resource.id] = resource
            return "registered"

    def generate_resource_map(self, resource_id):
        if not self.has_resource(resource_id):
            raise ResourceError(message="Unknown resource id")
        resource = self.get_resource(resource_id)
        resource_map = {
            "id": resource.id,
            "type": resource.type,
            "vocab": resource.vocab
        }
        for relation_type in resource.get_relations():
            resource_map[relation_type] = []
            for subresource in resource.get_subresources(relation_type):
                subresource_map = self.generate_resource_map(subresource.id)
                if subresource_map["vocab"] == resource.vocab:
                    del(subresource_map["vocab"])
                resource_map[relation_type] += [subresource_map]
        return resource_map

    def parse_resource_map(self, resource_map):
        self.check_required_properties(resource_map)
        self.vocab_store.register_vocabulary(resource_map['vocab'])
        self.check_resource_id_is_IRI(resource_map["id"])
        self.check_resource_type_is_valid(resource_map["type"])
        resource = self.make_resource(resource_map)
        subresources = self.parse_subresources(resource_map)
        resource.add_subresources(subresources)
        return resource

    def check_required_properties(self, resource_map):
        missing = ", ".join([key for key in self.required if key not in resource_map.keys()])
        if missing:
            message = 'resource is missing the following properties: %s' % (missing)
            raise ResourceError(message)

    def check_resource_id_is_IRI(self, resource_id):
        try:
            parse_IRI(resource_id)
        except ValueError:
            raise ResourceError(message = 'resource identifier is not an IRI: %s' % (resource_id))

    def check_resource_type_is_valid(self, resource_type):
        resource_class = self.vocab_store.lookupLabel(resource_type)
        if not resource_class or not self.vocab_store.is_class(resource_class):
            message="Illegal resource type: %s" % (resource_type)
            raise ResourceError(message)

    def make_resource(self, resource_map):
        if self.has_resource(resource_map["id"]):
            self.check_type_consistent(resource_map["id"], resource_map["type"])
            return self.get_resource(resource_map["id"])
        else: # only make a new resource when id is not previously registered
            return Resource(resource_map)

    def check_type_consistent(self, resource_id, resource_type):
        registered_type = self.get_resource_type(resource_id)
        if  registered_type != resource_type:
            message = "Conflicting resource types: resource %s is already registered as type %s and cannot be additionally registered as type %s" % (resource_id, registered_type, resource_type)
            raise ResourceError(message)

    def parse_subresources(self, resource_map):
        subresources = defaultdict(list)
        for relation_type in self.get_resource_relations(resource_map):
            for subresource_map in resource_map[relation_type]:
                subresource_map['vocab'] = resource_map['vocab']
                subresource = self.parse_resource_map(subresource_map)
                subresources[relation_type].append(subresource)
        return subresources

    def is_relation(self, label, resource_map):
        if label in self.required:
            return False # skip own properties
        subject = self.vocab_store.lookupLabel(label)
        # check if subject belongs to vocabulary specified in resource map
        # TO DO
        # check if subject is relation
        if not subject or not self.vocab_store.is_property(subject):
            message="Illegal resource relationship: %s" % (label)
            raise ResourceError(message)
        return True

    def get_resource_relations(self, resource_map):
        return [key for key in resource_map.keys() if self.is_relation(key, resource_map)]

    def dump_index(self):
        with open(self.resource_file, 'wb') as fh:
            pickle.dump(self.resource_index, fh)

    def load_index(self):
        try:
            with open(self.resource_file, 'rb') as fh:
                resource_index = pickle.load(fh)
            for resource_id in resource_index.keys():
                self.resource_index[resource_id] = resource_index[resource_id]
        except (FileNotFoundError, EOFError):
            pass

class ResourceError(Exception):
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



