

## Use case

+ A textual scholar wants to annotate various parts of a digital edition such that the annotations can be used and interpreted independent from the way the edition is displayed. The scholar wants to analyse aggregates of the annotations at different levels, e.g. all annotations on the entire resource, as well as only the annotations on specific parts, e.g. annotations on a specific translation, or on the metadata. 
+ A media scholar wants to annotate the representation of ethnic minorities on Dutch current affairs programs in the 1990s. For analysis the scholar wants to aggregate annotations both on individual recordings of a program as well as at the whole program level (e.g. all annotated recordings of that program).

## Requirements

+ each 

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

1. **All-in-one annotation**: each annotation contains the structure information about the resource in the annotation target, using selectors and refinements.

+ *pros*: 
	+ *Simplicity*: single data structure for exchange
	+ *Interpretation*: annotations require less context for interpretation
+ *cons*:
	+ *Separation of concerns*: server cannot reason over structure outside of annotations, should check for consistency across annotations with targets that share structural elements. 
	+ *Verbosity*: annotations contain more structural information than necessary for many contexts
	+ *Redundancy*: high duplication of structural information, all annotations on resource X contain the same structural information
	+ *Multiple parents*: a resource can be part of multiple collections

2. **Structure represented as annotation**:
3. **Separate representations**: structural information is represented in a different data structure, based on e.g. the Annotatable Thing ontology, IIIF Presentation model of FRBRoo.
	+ Client sends structural relations between each part and whole separately
	+ Client sends whole structure in on representation