import json
from json.decoder import JSONDecodeError
import rdflib
from rdflib import Graph, OWL, RDFS, RDF
from rdflib.term import Literal, URIRef
from rdflib.plugins.parsers.notation3 import BadSyntax

class VocabularyStore(object):

    def __init__(self, config):
        self.url_file = config["url_file"]
        self.triple_file = config["triple_file"]
        self.urls = []
        self.vocab = Graph()
        self.load_urls()
        self.load_store()

    def has_vocabulary(self, url=None):
        return url in self.urls

    def show_vocabularies(self):
        return self.urls

    def register_vocabulary(self, url):
        response = {"ignored": [], "registered": []}
        if self.has_vocabulary(url):
            return {"ignored": [url], "registered": []}
        else:
            self.parse_vocabulary(url)
            self.urls.append(url)
            response["registered"] += [url]
            self.handle_imports(url, response)
            self.save()
        return response

    def parse_vocabulary(self, vocab_file):
        try:
            file_format = rdflib.util.guess_format(vocab_file)
            self.vocab.load(vocab_file, format=file_format)
        except BadSyntax as error:
            raise VocabularyError(message = error.message)

    def handle_imports(self, vocab_file, response):
        for s, p, o in self.vocab.triples((URIRef(vocab_file), OWL.imports, None)):
            if not self.has_vocabulary(o.toPython()): # .toPython() to get plain URI string
                sub_response = self.register_vocabulary(o.toPython())
                response["ignored"] += sub_response["ignored"]
                response["registered"] += sub_response["registered"]
        return response

    def lookupLabel(self, term):
        subjects = [s for s in self.vocab.subjects(RDFS.label, Literal(term))]
        try:
            subject = subjects[0]
        except IndexError:
            subject = None
        return subject

    def is_class(self, subject):
        return self.vocab_has_triple(subject, RDF.type, OWL.Class)

    def is_property(self, subject):
        return self.vocab_has_triple(subject, RDF.type, OWL.ObjectProperty)

    def vocab_has_triple(self, subj, pred, obj):
        return len([t for t in self.vocab.triples((subj, pred, obj))]) > 0

    def load_urls(self):
        try:
            with open(self.url_file, 'rt') as fh:
                self.urls = json.load(fh)
        except (OSError, JSONDecodeError):
            pass

    def save(self):
        self.save_urls()
        self.save_store()

    def save_urls(self):
        with open(self.url_file, 'wt') as fh:
            json.dump(self.urls, fh)

    def save_store(self):
        with open(self.triple_file, 'wb') as fh:
            fh.write(self.vocab.serialize(format="n3"))

    def load_store(self):
        try:
            self.vocab.load(self.triple_file, format="n3")
            message = "Vcoabulary loaded"
        except FileNotFoundError:
            message = "Vocabulary store file doesn't exist yet"
        return message

class VocabularyError(Exception):
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
