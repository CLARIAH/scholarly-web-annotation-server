

## Use case

+ A textual scholar wants to annotate various parts of a digital edition such that the annotations can be used and interpreted independent from the way the edition is displayed. The scholar wants to analyse aggregates of the annotations at different levels, e.g. all annotations on the entire resource, as well as only the annotations on specific parts, e.g. annotations on a specific translation, or on the metadata. 
+ A media scholar wants to annotate the representation of ethnic minorities on Dutch current affairs programs in the 1990s. For analysis the scholar wants to aggregate annotations both on individual recordings of a program as well as at the whole program level (e.g. all annotated recordings of that program).

## Requirements

## Architecture and Responsibilities

+ the edition server is responsible for:
	+ serving up RDFa-enriched resources,
	+ determining the annotatable thing ontology and resource structure
+ the annotation client is responsible for:
	+ incorporation of resource structure and ontology in handling user annotations 
	+ communicating resource structure to annotation server
+ the annotation server is responsible for:
	+ reasoning over resource structure in collecting annotations related to a resource
