

## Use case

+ A textual scholar wants to annotate various parts of a digital edition such that the annotations can be used and interpreted independent from the way the edition is displayed. The scholar wants to analyse aggregates of the annotations at different levels, e.g. all annotations on the entire resource, as well as only the annotations on specific parts, e.g. annotations on a specific translation, or on the metadata. 
+ A media scholar wants to annotate the representation of ethnic minorities on Dutch current affairs programs in the 1990s. For analysis the scholar wants to aggregate annotations both on individual recordings of a program as well as at the whole program level (e.g. all annotated recordings of that program).

## Requirements

Desirable characteristics:

+ *Simplicity*: number and complexity of data structures needed for exchange. Less complex is preferred.
+ *Interpretation*: the extent to which an annotation is interpretable independently of the annotated resource. More interpretable is preferred.
+ *Separation of concerns*: the structural relations between annotatable resources are needed for aggregating annotations on a requested resource, they are provided by the responsible agent of the edition server. The annotations are created by the users of the annotated resource and bear on the resources themselves, not necessarily on their structural relations. The annotation server should treat structural relations between resources differently from annotations on resources. This separation of concerns should ideally be reflected in the data structures used for representing structure and annotation. Clear separation is preferred.
+ *Conciseness*: annotation targets should contain no more information than necessary for identification. More concise is preferred. 
+ *Redundancy*: the amount of duplication of structural information across representations in the annotation server.
+ *Multiple parents*: a resource can be part of multiple collections (resource re-use). It should be possible to represent multiple parentage in the annotation server, so that annotations can be aggregated for different parents. 
+ *Open standards*: the extent to which open standards are used in the exchange protocol. Open standards are preferred.
+ *Model fitness*: Existing standards may not always be a perfect fit for the scenario that needs to be modelled. It is preferred use models that fit the domain and scenario and allow communicating the appropriate semantics.


## Architecture and Responsibilities

+ **Editition server**: 
	+ serving up RDFa-enriched resources,
	+ determining the annotatable thing ontology and resource structure
+ **Annotation client**:
	+ incorporation of resource structure and ontology in handling user annotations 
	+ communicating resource structure to annotation server
+ **Annotation server**:
	+ reasoning over resource structure in collecting annotations related to a resource


## Representing Structure and Annotations

There are two general approaches to representing the resource structure in the context of annotation:

1. **Embedded**: embedding structural relation information in annotation targets.
2. **Structure as annotation**: representing structural relation information as separate annotation.
3. **Structure as separate model**: representing structural relation information in a separate data model.


### 1. Embedded

Each annotation contains the structure information about the resource in the annotation target, using selectors and refinements.

Example:

```json
{
  "@context": "http://www.w3.org/ns/anno.jsonld",
  "created": 1483949925,
  "body": [
    {
      "vocabulary": "DBpedia",
      "value": "Theo van Gogh (art dealer)",
      "purpose": "classifying",
      "id": "http://dbpedia.org/resource/Theo_van_Gogh_(art_dealer)"
    }
  ],
  "motivation": "classifying",
  "creator": "marijn",
  "type": "Annotation",
  "target": [
    {
      "type": "Text",
      "source": "urn:vangogh:let001",
      "selector": {
        "conformsTo": "http://boot.huygens.knaw.nl/annotate/vangoghontology.ttl#",
        "value": "urn:vangogh:let001.receiver",
        "type": "FragmentSelector"
      }
    }
  ],
  "id": "urn:uuid:8f62be7d-de56-464b-8d9a-5fb0b69fc00b"
}
```

+ *pros*: 
	+ *Simplicity*: It uses a single data structure for exchange.
	+ *Interpretation*: annotations require less context for interpretation.
	+ *Open standards*: Only the W3C Web Annotation standard is used. No home-grown models are used.
+ *cons*:
	+ *Separation of concerns*: server cannot reason over structure outside of annotations, should check for consistency across annotations with targets that share structural elements. 
	+ *Conciseness*: annotations contain more structural information than necessary for many contexts
	+ *Redundancy*: high duplication of structural information, all annotations on resource X contain the same structural information
	+ *Multiple parents*: annotations on the same resource made in a different contexts show different parentage (is maybe a positive aspect?). The server needs to break down the hierarchy of structural information to allow for traversal from multiple parents. 




### 2. Structure as annotation

A structural relation between a resource and a sub-resource is represented as an annotation.

Example annotation:

```json
{
  "@context": "http://www.w3.org/ns/anno.jsonld",
  "created": 1483949925,
  "body": [
    {
      "vocabulary": "DBpedia",
      "value": "Theo van Gogh (art dealer)",
      "purpose": "classifying",
      "id": "http://dbpedia.org/resource/Theo_van_Gogh_(art_dealer)"
    }
  ],
  "motivation": "classifying",
  "creator": "marijn",
  "type": "Annotation",
  "target": [
    {
      "id": "urn:vangogh:let001.receiver",
      "type": "Text"
    }
  ],
  "id": "urn:uuid:8f62be7d-de56-464b-8d9a-5fb0b69fc00b"
}
```

Example structural relation:

```json
{
  "@context": "http://www.w3.org/ns/anno.jsonld",
  "created": 1483949925,
  "body": [
    {
      "vocabulary": "http://boot.huygens.knaw.nl/annotate/vangoghontology.ttl#",
      "id": "urn:vangogh:let001.receiver"
    }
  ],
  "motivation": "linking",
  "creator": "marijn",
  "type": "Annotation",
  "target": [
    {
      "id": "urn:vangogh:let001",
    }
  ],
  "id": "urn:uuid:8f62be7d-de56-464b-8d9a-5fb0b70fc00b"
}
```


+ *pros*:
	+ *Simplicity*: all representations are W3C annotations.
	+ *Redundancy*: Each relation is stored only once, resulting in low redundancy.
	+ *Conciseness*: Lazy storing of resource structure, i.e. only the structural relations of annotated (sub-)resources are stored. 
	+ *Open standards*: Only the W3C Web Annotation standard is used. No home-grown models are used.

+ *Cons*:
	+ *Conciseness*: each structural relation is sent as a separate representation with unnecessary W3C annotation metadata. 
	+ *Separation of concerns*: The representations do no reflect the different natures of annotations and structural relations.
	+ *Open standards*: The Web Annotation model is used differently from its intended purpose, namely to describe structural information.



### 3. Structure as Separate Model

Structural information is represented in a different data structure, based on e.g. the Annotatable Thing ontology, or using an existing data model such as the [IIIF Presentation model](http://iiif.io/api/presentation/2.1/) or [Schema.org](http://schema.org).

There are multiple options for exchanging structural information between annotation server and client:

+ *Lazy, partial, atomic*: client sends only structural relations between annotated target and its ancestors, each parent-child relation as separate data structure. The server stores each relation directly.
+ *Lazy, partial, composite*: client sends only structural relations between annotated target and its ancestors, all parent-child relations in one hierarchical data structure. The server parses the hierarchy and stores individual relations.
+ *Pro-active, complete, composite*: client sends whole resource structure to server, either upon loading a resource, regardless of whether a user makes an annotation, 
+ *Lazy, complete, composite*: client sends whole resource structure to server together with a new or updated annotation, regardless of which (sub-)resource is the annotation target. 

#### 1. Structural representation via Annotatable Thing Ontology:

```json
{
  "@context": "http://boot.huygens.knaw.nl/annotate/vangoghontology.ttl#", 
  "@type": "Letter", 
  "id": "urn:vangogh:letter001", 
  "hasMetadataItem": [
	{
      "@id": "urn:vangogh:letter001.sender", 
      "@type": "Sender", 
    },
	{
      "@id": "urn:vangogh:letter001.receiver", 
      "@type": "Receiver", 
    },
	{
      "@id": "urn:vangogh:letter001.date", 
      "@type": "Date", 
    },
  ],
  "hasPart": [
	{
      "@id": "urn:vangogh:letter001:p.1", 
      "@type": "ParagraphInLetter", 
    },
	{
      "@id": "urn:vangogh:letter001:p.2", 
      "@type": "ParagraphInLetter", 
    },
	{
      "@id": "urn:vangogh:letter001:p.3", 
      "@type": "ParagraphInLetter", 
    },
  ],
  "hasNote": [
	{
      "@id": "urn:vangogh:letter001:note.1", 
      "@type": "Note", 
    },
	{
      "@id": "urn:vangogh:letter001:note.2", 
      "@type": "Note", 
    },
	{
      "@id": "urn:vangogh:letter001:note.3", 
      "@type": "Note", 
    },
  ],
  "hasEnrichment": [
	{
      "@id": "urn:vangogh:letter001.translation", 
      "@type": "CreativeWork Translation", 
      "hasPart": [
		{
	      "@id": "urn:vangogh:letter001:translation:p.1", 
	      "@type": "ParagraphInLetter", 
	    },
		{
	      "@id": "urn:vangogh:letter001:translation:p.2", 
	      "@type": "ParagraphInLetter", 
	    },
		{
	      "@id": "urn:vangogh:letter001:translation:p.3", 
	      "@type": "ParagraphInLetter", 
	    },
	  ],
	  "hasNote": [
		{
	      "@id": "urn:vangogh:letter001:translation:note.1", 
	      "@type": "Note", 
	    },
		{
	      "@id": "urn:vangogh:letter001:translation:note.2", 
	      "@type": "Note", 
	    },
		{
	      "@id": "urn:vangogh:letter001:translation:note.3", 
	      "@type": "Note", 
	    },
	  ],
    },
  ]
}
```

+ *Pros*:
	+ *Simplicity*: the structural representation can lean entirely on the ontology used to describe the resource (responsibility of the resource server).
	+ *Conciseness*: the structural representation only contains structural information. In the above example it is possible to leave out the `@type` information to leave only the relationship information.
+ *Cons*:
	+ *Open standards*: It introduces a new ontology. **Note**: it is possible for resource/edition servers to use existing ontologies (e.g. Schema.org) 

#### 2. Structural representation via IIIF

An example has been worked out in the IIIF analysis document, in the section [IIIF Collections and Manifests](https://github.com/marijnkoolen/rdfa-annotation-client/blob/master/discussion/comparing-iiif-and-web-annotation-models.md#iiif_model).

+ *Pros*:
	+ *Open standards*: makes use of existing standard for representing structure. 
+ *Cons*:
	+ *Open standards*: uses standard for other than intended purpose (IIIF Presentation API is intended for image viewers to understand structure of images representing an object).
	+ *Simplicity*: It introduces two types of structural elements, i.e. collections and manifests.
	+ *Conciseness*: The IIIF model generates a lot of overhead to represent simple relationships, mainly because it is intended to provide display information in manifests.


#### 3. Structural representation via [Schema.org]()

An alternative to using our own annotatable thing ontology is to rely on [Schema.org](http://schema.org/). For instance, the van Gogh correspondence can be modelled using a combination of a number of pre-defined schemas:

+ [Message](http://schema.org/Message), [TranslationOfWork](http://bib.schema.org/workTranslation) and [Painting](http://schema.org/Painting) (for paintings mentioned in letters)

```json
{
  "@context": "http://schema.org/",
  "@type": "Message",
  "id": "urn:vangogh:letter001",
  "hasPart": [
    {
      "id": "urn:vangogh:letter001.sender",
    },
    {
      "id": "urn:vangogh:letter001.receiver",
    },
    {
      "id": "urn:vangogh:letter001.date",
    },
    {
      "id": "urn:vangogh:letter001.locationnote",
    },
    {
      "id": "urn:vangogh:letter001.sourcenote",
    },
    {
      "id": "urn:vangogh:letter001:p.1",
    },
    {
      "id": "urn:vangogh:letter001:p.2",
    },
    {
      "id": "urn:vangogh:letter001:p.3",
    },
    {
      "id": "urn:vangogh:letter001:p.4",
    },
    {
      "id": "urn:vangogh:letter001:p.5",
    },
    {
      "id": "urn:vangogh:letter001:p.6",
    },
    {
      "id": "urn:vangogh:letter001:p.7",
    } 
    {
      "id": "urn:vangogh:letter001:note.1",
    },
    {
      "id": "urn:vangogh:letter001:note.2",
    },
    {
      "id": "urn:vangogh:letter001:note.3",
    },
    {
	  "@type": "TranslationOfWork",
	  "id": "urn:vangogh:letter001.translation",
	  "hasPart": [
        {
          "id": "urn:vangogh:letter001:p.1",
		},
		{
		  "id": "urn:vangogh:letter001:p.2",
		},
		{
		  "id": "urn:vangogh:letter001:p.3",
		},
		{
		  "id": "urn:vangogh:letter001:p.4",
		},
		{
		  "id": "urn:vangogh:letter001:p.5",
		},
		{
		  "id": "urn:vangogh:letter001:p.6",
		},
		{
		  "id": "urn:vangogh:letter001:p.7",
        }
      ]
    }
  ]
}
```

This schema also has properties `sender` , `recipient` and `dateCreated`, but it's probably clearer to just refer to all sub-resources as parts. 

+ *pros*: 
	+ *Open standards*: it uses an open standard for communicating structure as well as for annotation.
+ *Cons*:
	+ *Open standards*: it uses default schema inappropriately and doesn't allow for any specific ontology properties used in editions.

## Further reading

#### FRBR

+ [FRBR in JSON-LD markup examples](http://json-ld.org/spec/ED/json-ld-syntax/20100529/#markup-examples)
+ [Expression of Core FRBR Concepts in RDF](http://vocab.org/frbr/)
+ [Bibliographic Framework as Web of Data](https://www.loc.gov/bibframe/pdf/marcld-report-11-21-2012.pdf)
+ [Essential FRBR in OWL2 DL Ontology (FRBR DL)](http://www.sparontologies.net/ontologies/frbr)
+ [IFLA overview page for FRBRoo](http://www.ifla.org/node/10171)
+ [Definition of Object-Oriented FRBR](http://www.ifla.org/files/assets/cataloguing/FRBRoo/frbroo_v_2.4.pdf)

#### Europeana Data Model

+ [EDM documentation](http://pro.europeana.eu/share-your-data/data-guidelines/edm-documentation)
+ [record properties](http://labs.europeana.eu/api/record), [JSON-LD version](http://labs.europeana.eu/api/record-jsonld)
+ [hierarchical records](http://labs.europeana.eu/api/hierarchical-records)

#### Schema.org

+ [Overview of schemas](http://schema.org/docs/schemas.html)
+ [Data Model](http://schema.org/docs/datamodel.html)
+ Example: [Scholarly article](http://schema.org/ScholarlyArticle)