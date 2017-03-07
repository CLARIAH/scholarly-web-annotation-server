# Dealing with Resource Structure for Annotations

### Table of Contents

1. [Use Cases](#use_cases)
2. [Requirements](#requirements)
	+ 2.1 [Annotation Functionalities](#annotation_functionalities)
	+ 2.2 [Domain constraints](#domain_constraints)
	+ 2.3 [Domain model characteristics](#domain_characteristics)
3. [Architecture and Responsibilities](#responsibilities)
4. [Representing Annotations and Resource Structure](#representing)
	+ 4.1 [Desirable data model characteristics](#desirable_characteristics)
	+ 4.2 [Structure Embedded in Annotation](#representing_embedded)
	+ 4.3 [Structure as Separate Annotation](#representing_as_annotation)
	+ 4.4 [Structure as Separate Model](#representing_as_model)
		+ 4.4.1 [Annotatable Thing Ontology](#representing_as_annotatable_thing)
		+ 4.4.2 [Annotatable Thing Ontology as Abstract Class](#representing_as_abstract_class)
		+ 4.4.3 [IIIF](#representing_as_iiif)
		+ 4.4.4 [Schema.org](#representing_as_schema)
	+ 4.5 [Ranking Modelling Options](#ranking_options)
5. [Further reading](#reading)
	+ 5.1 [FRBR and FRBRoo](#reading_frbr)
	+ 5.2 [Europeana Data Model](#reading_edm)
	+ 5.3 [Schema.org](#reading_schema)
	+ 5.4 [IIIF](#reading_iiif)


<a name="use_cases"></a>
## 1. Use cases

The initial use case for this project was presented at [IAnnotate 2016 by Peter Boot](https://www.youtube.com/watch?v=PHTdfiZoNto):

+ A textual scholar wants to annotate various parts of a digital scholarly edition of the [Correspondence of Vincent van Gogh](http://vangoghletters.org/vg/), such that the annotations can be used and interpreted independent from the way the edition is displayed. The scholar wants to analyse aggregates of the annotations at different levels, e.g. all annotations on an entire resource such as a letter, as well as only the annotations on specific parts, e.g. annotations on a specific translation of that letter, on a fragment of a single paragraph, or on its metadata. 

Potential other use cases: 

+ A media scholar wants to annotate the representation of ethnic minorities on Dutch current affairs TV and radio programs in the 1990s. For analysis the scholar wants to aggregate annotations both on individual recordings of a program as well as at the whole program level (e.g. all annotated recordings of that program). This use case is derived from [Melgar et al. (2017)](http://humanities.uva.nl/~mkoolen1/publications/2017/melg:proc17.pdf)

+ A historian wants to investigate uses of medical drug components in the domains of science, commerce and public debate in the period 1500-1800 and wants to annotate relevant passages in newspaper articles, books and pamphlets. On top of the annotated passages, the researchers wants to annotate mentions of medical drug components, and other entities related to the events they are involved, including people, organisations, locations, actions and objects. During the research process, the historian wants to query the annotation server for various subsets of the annotations for analysis, aggregating the annotations on e.g. the newspaper they appeared in or the type of entities or events annotated. 

<a name="requirements"></a>
## 2. Requirements

The annotation client is loaded in a browser window together with one or more resources, marked up with structural information embedded RDFa, that can be annotated. Each top-level resource in the browser window can have individually annotatable sub-resources.

<a name="annotation_functionalities"></a>
### 2.1 Annotation Functionalities

The annotation client should be able to:

+ retrieve existing annotations on a top-level resource in the browser window as well as annotations on any of its annotatable sub-resources, and annotations on top of those annotations (stacked annotations). 
+ retrieve and process information from the ontology that is used to describe the structure of the resource, and be able to 1) identify annotatable and non-annotatable elements, as well as make identify which (sub-)resources can only be annotated as a whole.

<a name="domain_constraints"></a>
### 2.2 Domain constraints

The requirements above provide few constraints on what structures of resources and sub-resources are possible. In principle, resources could be linked in cycles, where for instance one digital edition represents the the translation of a letter is a sub-resource of the original letter, but a different edition may represent the original as sub-resource of the translation. 

To ensure a clearly defined and computationally tractable set of annotations to retrieve for a given resources, it's desirable to avoid cycles in resource relational structure. Therefore, we propose the follow constraints:

+ Resources and annotations are considered different types, whereby resources can only link to sub-resources, whereas annotations can link to resources *and* to already-existing annotations. This results in a **two-type network**. 
+ Sub-resources cannot link to higher-level resources, to avoid cycles. This design decision brings certain limitations of what can be modelled, but helps to frame the problem and limits the problem space. 
+ Annotations can themselves become resources (changing their type and switching to the other side of the two-type network), but only through editorial decisions. [not sure about the following constraint]: This makes the annotation into a publicly visible resource. The annotation becomes a sub-resources of the resource it annotations.

<a name="domain_characteristics"></a>
### 2.3 Domain model characteristics

The domain constraints described above have a number of consequences for the domain model:

+ Resource and their sub-resources form trees. 
+ Resources can be grouped in arbitrary(?) collections, where individual resources can belong to multiple collections. 
+ A consequence of allowing arbitrary collections is that resources trees can be grouped in such as way that resources can have multiple parents. Instead of a *forest*, the resulting structure of trees is a [Direct Acyclic Graph](https://en.wikipedia.org/wiki/Directed_acyclic_graph) (DAG). 
+ Annotations can target one or more resources and/or one or more annotations. 
+ Annotations can be targeted by multiple other annotations (multiple parentage). 
+ The annotation graph is therefore also a DAG. However, the endpoint of a directed chain of annotations is always a *resource*.
+ Annotations can only target existing annotations, so the graph is also temporally ordered. 
+ A chain of annotations always ends in leaf annotations that target *resources*.
+ This results in a single graph structure. It is not a [bipartite graph](https://en.wikipedia.org/wiki/Bipartite_graph), because 1) among resources links are always between nodes of the same type, namely resource-to-resource, 2) annotations can link to both resources and annotations.  

<a name="responsibilities"></a>
## 3. Architecture and Responsibilities

In Peter's IAnnotate presentation, he suggested three

+ **Editition server**: 
	+ serve up an edition (or more generally, a resource) to a user in a browser,
	+ determine what parts of the edition/resource can be annotated, specified in an [Annotatable Thing ontology](http://boot.huygens.knaw.nl/annotate/genericontology.ttl) and any extension for specific domain (e.g [Van Gogh Ontology](boot.huygens.knaw.nl/annotate/vangoghontology.ttl)), 
	+ embed the structural information of the resource through RDFa properties in the HTML representation.
	
+ **Annotation client**:
	+ runs in the browser and is embedded in edition/resource.
	+ incorporates the resource structure and ontology in handling user annotations,
	+ deals with non-annotatable parts of a resource and with resources that can only be targeted as a whole, 
	+ exchanges annotations and resource structure with the annotation server.

+ **Annotation server**:
	+ reasons over resource structure in storing and retrieving annotations related to a resource.
	+ exchanges annotations and resource structure with the annotation client.


<a name="representing"></a>
## 4. Representing Structure and Annotations

There are two general approaches to representing the resource structure in the context of annotation:

1. **Structure Embedded in Annotation**: embedding structural relation information in annotation targets.
2. **Structure as Separate Annotation**: representing structural relation information as separate annotation.
3. **Structure as Separate Model**: representing structural relation information in a separate data model.

<a name="desired_characteristics"></a>
### 4.1 Desirable data model characteristics

The annotation client and server have to use an exchange protocol and data model to exchange information about annotations and resources. Below are a (rather ad hoc) list of characteristics by which to compare different data models and help decide on a model that best fits the problem domain and constraints. 

+ *Simplicity*: number and complexity of data structures needed for exchange. Less complex is preferred.
+ *Interpretation*: the extent to which an annotation is interpretable independently of the annotated resource. More interpretable is preferred.
+ *Separation of concerns*: the structural relations between annotatable resources are needed for aggregating annotations on a requested resource, they are provided by the responsible agent of the edition server. The annotations are created by the users of the annotated resource and bear on the resources themselves, not necessarily on their structural relations. The annotation server should treat structural relations between resources differently from annotations on resources. This separation of concerns should ideally be reflected in the data structures used for representing structure and annotation. Clear separation is preferred.
+ *Conciseness*: annotation targets should contain no more information than necessary for identification. More concise is preferred. 
+ *Redundancy*: the amount of duplication of structural information across representations in the annotation server.
+ *Multiple parents*: a resource can be part of multiple collections (resource re-use). It should be possible to represent multiple parentage in the annotation server, so that annotations can be aggregated for different parents. 
+ *Open standards*: the extent to which open standards are used in the exchange protocol. Open standards are preferred.
+ *Model fitness*: Existing standards may not always be a perfect fit for the scenario that needs to be modelled. It is preferred to use models that fit the domain and scenario and allow communicating the appropriate and necessary semantics.



<a name="representing_embedded"></a>
### 4.2. Structure Embedded in Annotation

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
	+ *Multiple parents*: annotations on the same resource made in a different contexts show different parentage (is maybe a positive aspect?). To allow for traversal from the requested resource to a descendant resource, the server needs to break down the hierarchy of structural information in each annotation target and store the relations between hierarchically related (sub-)resources. 




<a name="representing_as_annotation"></a>
### 4.3. Structure as Separate Annotation

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
	+ *Multiple parents*: Each hierarchical relationship is send as separate annotation, so the server can traverse from different ancestors to the same descendant resource.

+ *Cons*:
	+ *Conciseness*: each structural relation is sent as a separate representation with unnecessary W3C annotation metadata. This generates a load of overhead in transmitted data.
	+ *Separation of concerns*: The representations do no reflect the different natures of annotations and structural relations.
	+ *Model fitness*: The Web Annotation model is used differently from its intended purpose, namely to describe structural information that should not be displayed to the user.


<a name="representing_as_model"></a>
### 4.4. Structure as Separate Model

Structural information is represented in a different data structure, based on e.g. the Annotatable Thing ontology, or using an existing data model such as the [IIIF Presentation model](http://iiif.io/api/presentation/2.1/) or [Schema.org](http://schema.org).

There are multiple options for exchanging structural information between annotation server and client:

+ *Lazy, partial, atomic*: client sends only structural relations between annotated target and its ancestors, each parent-child relation as separate data structure. The server stores each relation directly.
+ *Lazy, partial, composite*: client sends only structural relations between annotated target and its ancestors, all parent-child relations in one hierarchical data structure. The server parses the hierarchy and stores individual relations.
+ *Pro-active, complete, composite*: client sends whole resource structure to server, either upon loading a resource, regardless of whether a user makes an annotation, 
+ *Lazy, complete, composite*: client sends whole resource structure to server together with a new or updated annotation, regardless of which (sub-)resource is the annotation target. 

In the various options below, the information about the hierarchical structure of resources that is sent between client and server
The example annotation below, identifying the paragraph in the translation of a letter that contains the salutation, is used to compare the different models for handling hierarchical structure:

```json
{
  "@context": "http://www.w3.org/ns/anno.jsonld",
  "created": 1483949925,
  "body": [
    {
      "vocabulary": "DBpedia",
      "value": "Salutation",
      "purpose": "classifying",
      "id": "http://dbpedia.org/resource/Salutation"
    }
  ],
  "motivation": "classifying",
  "creator": "marijn",
  "type": "Annotation",
  "target": [
    {
      "id": "urn:vangogh:let001:translation:p.2",
      "type": "Text"
    }
  ],
  "id": "urn:uuid:8f62be7d-de56-464b-8d9a-5fb0b69fc00b"
}
```

The target is the URN of the second paragraph of the English translation of the letter that is originally written in Dutch. All information regarding the relation between the annotated paragraph and the original letter, its translation and the larger correspondence should be handled separately in a structure-oriented data model.

<a name="representing_as_annotatable_thing"></a>
#### 4.4.1. Structural representation via Annotatable Thing Ontology:

A straightforward way for the client to communicate structural information about the resource is to send the RDFa information of a resource using the vocabulary that it's based on as context. In that case of the *van Gogh Correspondence*, this is the Annotatable Thing ontology created by Peter Boot:

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

The annotation server can store all structural relations including those between the original letter and its translation, and between the translation and its second paragraph. This allows traversal from any of these three resources to the annotation about the salutation.

+ *Pros*:
	+ *Simplicity*: the structural representation can lean entirely on the ontology used to describe the resource (responsibility of the resource server).
	+ *Conciseness*: the structural representation only contains structural information. In the above example it is possible to leave out the `@type` information to leave only the relationship information.
	+ *Open standards*: In a way this is the most flexible and open, as it allows use of different ontologies. The main point is that the server should know how to interpret relationships like `hasEnrichment` and `hasNote`, but perhaps it needs nothing more than to use these as edge labels (it can find out about their inverse, e.g. `isPartOf` from the `@context`.
	+ *Separation of concerns*: hierarchal resource structure is modelled differently from annotations, there can naturally be handled differently by the server. 
	+ *Model fitness*: this makes full use of the annotation ontology and allows the server to use the same structure-related semantics as the client. 
+ *Cons*:
	+ *Open standards*: It introduces the annotatable thing ontology as yet another new ontology. **Note**: it is possible for resource/edition servers to use existing ontologies (e.g. Schema.org). 
	+ *Redundancy*: The client sends the entire resource structure to the server upon parsing the resource in the browser window, regardless of whether the server already knows about the resource structure. 

**Note**: as the structure of the letter is based on a template, it feels verbose to send all structural connections for each individual letter. For *conciseness*, it would be better if only a reference to the ontology would suffice. 


<a name="representing_as_abstract_class"></a>
#### 4.4.2. Using the Annotatable Ontology as an abstract class

An question to consider is whether it is possible and preferable to send only (a reference to) the ontology as an abstract class that explains the structural relations, such that the server knows that a `letter` has a `sender` and a `receiver` without having to explicitly receive and store all the relations between the URNs of the sub-resources. 

The gain would be that potentially less information is sent by the client. However, if the ontology is very elaborate or complex while individual resources based on it are typically much simpler, it might require a smaller payload to send only the few resource IRIs and their structural relations. 

To work with ontologies as abstract classes, the annotations themselves should also rely on ontology information, that is, use the URN of the letter as target and use the path to the annotated sub-resource(s) as selectors within that target. There are several problems that need to be solved are.

+ *Pros*:
	+ *Conciseness*: In principle, the client only has to send the URL for the `@context` to the server, both when retrieving existing annotations and submitting new annotations. 
	+ *Redundancy*: The server can check if it knows about the `@context` already so only has to retrieve and parse that `@context` once (perhaps with a temporal update threshold to check if the `@context` has changed since the last check).
	+ 	*Separation of concerns*: Hierarchical resource structure is modelled differently from annotations, so can naturally be handled separately.
+ *Cons*:
	+ *Disambiguation*: how to refer to a specific sub-resource that is part of a list of sub-resources of the same type, at the same structural level. For instance, the example letter has 7 paragraphs. How should the annotation target identify the *n-th* paragraph in that list? More problematically, what information should the client send when the target is the *n-th* paragraph of the translation of the letter? 
	+ *Multiple parents*: if the translation of a letter is a sub-resource of that letter as well as of a collection of translations, then how should it be represented as an annotation target? The translation is a resource in its own right (it's a creative work) and can use the same ontology as template (e.g. it is a letter with paragraphs and notes as sub-resources). If only the translation is displayed so that the annotation client only sees the translation as top-level resource, how should the client communicate that a paragraph in that translation is part of the original letter? 
	+ *Simplicity*: For multilevel hierarchies, the annotation should contain all the structural information between the lowest level base target and the deepest level sub-resource at which the annotation is made.

In way, using the ontology as an abstract class requires a similar solution as the **All-in-one** approach: the entire path from the *top* resource (i.e. the letter) to the annotated sub-resource (e.g. a paragraph in the translation of the letter) has to be represented in the annotation target. An unsolved problem remains with identifying the relation between a translation of a letter and its original when only the translation is displayed: does it have its own URN? If so, how is its relation with the original letter stored via the abstract class?

<a name="representing_as_iiif"></a>
#### 4.4.3. Structural representation via IIIF

An example has been worked out in the IIIF analysis document, in the section [IIIF Collections and Manifests](https://github.com/marijnkoolen/rdfa-annotation-client/blob/master/discussion/comparing-iiif-and-web-annotation-models.md#iiif_model).

+ *Pros*:
	+ *Open standards*: makes use of existing standard for representing structure. 
	+ *Multiple parents*: Multiple collections can contain the same (sub-)resource, so travel from different ancestors to the same descendant is not problematic.
	+ *Separation of concerns*: Hierarchical resource structure is modelled differently from annotations, so can naturally be handled separately.
+ *Cons*:
	+ *Model fitness*: uses standard for other than intended purpose (IIIF Presentation API is intended for image viewers to understand structure of images representing an object).
	+ *Simplicity*: It introduces two types of structural elements, i.e. collections and manifests.
	+ *Conciseness*: The IIIF model generates a lot of overhead to represent simple relationships, mainly because it is intended to provide display information in manifests.
	+ *Redundancy*: A huge of amount of unnecessary information about a resource is sent every time the client retrieves or submits annotations.


<a name="representing_as_schema"></a>
#### 4.4.4. Structural representation via Schema.org

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
	+ *Conciseness*: the structural representation only contains structural information. 
	+ *Separation of concerns*: Hierarchical resource structure is modelled differently from annotations, so can naturally be handled separately.
	+ *Multiple parents*: Multiple collections can contain the same (sub-)resource, so travel from different ancestors to the same descendant is not problematic.

+ *Cons*:
	+ *Model fitness*: it uses default schema inappropriately and doesn't allow for any specific ontology properties used in editions.
	+ *Redundancy*: The client sends the entire resource structure to the server upon parsing the resource in the browser window, regardless of whether the server already knows about the resource structure. 
	+ *Simplicity*: It's not obvious what schema to use if the resource server doesn't specify this. E.g. in the Correspondence case the most appropriate schema might be message, but in the case of newspaper articles, it is probably a different schema. An alternative is to always use the `Thing` because it contains the `hasPart` relationship, but it doesn't allow any subtle semantics of the domain.

<a name="ranking_options"></a>
### 4.5 Ranking Modelling Options

The first two options (**All-in-one** and **Structure as annotation**) lead to severe problems:

+ **All-in-one** forces the server to parse annotations to reason over structure, has high duplication and doesn't easily generalise aggregation at larger levels (multiple parents).
+ **Structure as annotation** has high overhead in exchanging information, doesn't clearly separate resource structure information from annotations and doesn't fit well with the purposes of the W3C Web Annotation model. 

Of the **Structure as separate model** options, the **IIIF** and **Annotation as Abstract Class** models have severe problems:

+ The **IIIF** case has enormous overhead and makes inappropriate use of an open standard.
+ The **Annotation as Abstract Class** model has similar issues as the **All-in-one** approach.

From the above, it seems that the most viable options is to use the *Annotatable Thing* ontology as a context to represent resource structure. Perhaps this could be treated as a special case of Schema.org as a specific schema for annotation. Alternatively, it could be seen as a general ontology that can be extended with domain-specific schemas from Schema.org. 


<a name="reading"></a>
## 5. Further reading

<a name="reading_frbr"></a>
### 5.1 FRBR

+ [FRBR in JSON-LD markup examples](http://json-ld.org/spec/ED/json-ld-syntax/20100529/#markup-examples)
+ [Expression of Core FRBR Concepts in RDF](http://vocab.org/frbr/)
+ [Bibliographic Framework as Web of Data](https://www.loc.gov/bibframe/pdf/marcld-report-11-21-2012.pdf)
+ [Essential FRBR in OWL2 DL Ontology (FRBR DL)](http://www.sparontologies.net/ontologies/frbr)
+ [IFLA overview page for FRBRoo](http://www.ifla.org/node/10171)
+ [Definition of Object-Oriented FRBR](http://www.ifla.org/files/assets/cataloguing/FRBRoo/frbroo_v_2.4.pdf)

<a name="reading_edm"></a>
### 5.2 Europeana Data Model

+ [EDM documentation](http://pro.europeana.eu/share-your-data/data-guidelines/edm-documentation)
+ [record properties](http://labs.europeana.eu/api/record), [JSON-LD version](http://labs.europeana.eu/api/record-jsonld)
+ [hierarchical records](http://labs.europeana.eu/api/hierarchical-records)

<a name="reading_schema"></a>
### 5.3 Schema.org

+ [Overview of schemas](http://schema.org/docs/schemas.html)
+ [Data Model](http://schema.org/docs/datamodel.html)
+ Example: [Scholarly article](http://schema.org/ScholarlyArticle)


<a name="reading_iiif"></a>
### 5.4 IIIF

+ [IIIF](http://iiif.io/)
	+ APIs: [Image](http://iiif.io/api/image/2.1/), [Presentation](http://iiif.io/api/presentation/2.1/), [Search](http://iiif.io/api/search/2.1/)
+ IXIF
	+ [IXIF Interim Implementation](https://gist.github.com/tomcrane/7f86ac08d3b009c8af7c)
	+ [Sound and Vision blog post on IXIF](https://www.beeldengeluid.nl/en/blogs/research-amp-development-en/201604/interweaving-online-media-ixif)
+ [Universal Viewer](http://universalviewer.io/)