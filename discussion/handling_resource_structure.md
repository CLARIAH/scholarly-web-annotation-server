

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

#### All-in-one annotation

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
	+ *Simplicity*: single data structure for exchange
	+ *Interpretation*: annotations require less context for interpretation
+ *cons*:
	+ *Separation of concerns*: server cannot reason over structure outside of annotations, should check for consistency across annotations with targets that share structural elements. 
	+ *Conciseness*: annotations contain more structural information than necessary for many contexts
	+ *Redundancy*: high duplication of structural information, all annotations on resource X contain the same structural information
	+ *Multiple parents*: annotations on the same resource made in a different contexts show different parentage (is maybe a positive aspect?). The server needs to break down the hierarchy of structural information to allow for traversal from multiple parents. 




#### Structure represented as annotation

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


*pros*:

+ *Simplicity*: all representations are W3C annotations.
+ *Redundancy*: Each relation is stored only once, resulting in low redundancy.
+ *Conciseness*: Lazy storing of resource structure, i.e. only the structural relations of annotated (sub-)resources are stored. 

*Cons*:

+ *Conciseness*: each structural relation is sent as a separate representation with unnecessary W3C annotation metadata. 
+ *Separation of concerns*: The representations do no reflect the different natures of annotations and structural relations.



#### Separate representations

Structural information is represented in a different data structure, based on e.g. the Annotatable Thing ontology, or using an existing data model such as the [IIIF Presentation model](http://iiif.io/api/presentation/2.1/) or [FRBRoo](http://www.ifla.org/files/assets/cataloguing/FRBRoo/frbroo_v_2.4.pdf).

There are multiple options for exchanging structural information between annotation server and client:

+ *Lazy, partial, atomic*: client sends only structural relations between annotated target and its ancestors, each parent-child relation as separate data structure. The server stores each relation directly.
+ *Lazy, partial, composite*: client sends only structural relations between annotated target and its ancestors, all parent-child relations in one hierarchical data structure. The server parses the hierarchy and stores individual relations.
+ *Complete, composite*: client sends whole resource structure to server, either upon loading a resource (*pro-active*: even without a user making an annotation), or together with a new or updated annotation (*lazy*), regardless of which sub-resource is the annotation target. 