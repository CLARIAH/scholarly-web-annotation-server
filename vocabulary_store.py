import rdflib
from rdflib import Graph, OWL, RDFS, RDF
from rdflib.term import Literal, URIRef
from rdflib.plugins.parsers.notation3 import BadSyntax

class VocabularyStore(object):

    def __init__(self):
        self.urls = []
        self.vocab = Graph()

    def register_vocabulary(self, url):
        if self.has_vocabulary(url):
            return {"message": "ontology already regsitered"}
        self.parse_vocabulary(url)
        self.urls.append(url)
        return {"message": "ontology registered"}

    def has_vocabulary(self, url=None):
        return url in self.urls

    def show_vocabularies(self):
        return self.urls

    def parse_vocabulary(self, vocab_file):
        try:
            file_format = rdflib.util.guess_format(vocab_file)
            self.vocab.load(vocab_file, format=file_format)
        except BadSyntax as error:
            raise InvalidVocabularyError(message = error.message)
        self.handle_imports(vocab_file)

    def handle_imports(self, vocab_file):
        for s, p, o in self.vocab.triples((URIRef(vocab_file), OWL.imports, None)):
            if not self.has_vocabulary(o.toPython()): # .toPython() to get plain URI string
                self.register_vocabulary(o.toPython())

    def lookupLabel(self, term):
        subjects = [s for s in self.vocab.subjects(RDFS.label, Literal(term))]
        try:
            subject = subjects[0]
        except IndexError:
            subject = None
        return subject

    def is_property(self, subject):
        return self.vocab_has_triple(subject, RDF.type, OWL.ObjectProperty)

    def vocab_has_triple(self, subj, pred, obj):
        return len([t for t in self.vocab.triples((subj, pred, obj))]) > 0

class InvalidVocabularyError(Exception):
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
