# Alexandria and RDFa-based Web Annotation

The purpose of this document is to analyse the gap between Alexandria and the RDFa Annotation Client. [Alexandria](http://huygensing.github.io/alexandria/) is a text repository and annotation server. The RDFa Annotation Client adopts a new approach to annotations that Alexandria was not designed for. If we want to use Alexandria as the annotation server to support the client and this approach, adjustments have to be made to Alexandria to fit the requirements. 


### W3C Web Annotation Model

The client sends and accepts annotations that are in the format of the [W3C Web Annotation Model](https://www.w3.org/TR/annotation-model/#annotations). Currently, Alexandria only implements a part of this standard, namely, to [support IIIF annotation lists](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/webannotation/WebAnnotation.html).

How much of the Web Annotation model is needed in Alexandria for the RDFa annotation approach to work?

- **body and target**: [standard properties of bodies and targets](https://www.w3.org/TR/annotation-model/#bodies-and-targets)
- **target selector**:
	- *selectors*: Media Fragments, TextPositionSelector, TextQuoteSelector
	- *refinements*: i.e. multiple, hierarchically ordered selectors using the `refinedBy` property. **Note**: This should not be needed with the RDFa approach, as the `source` of the selector should be the most specific sub-resource.
- **motivation**: the Web Annotation standard has [a fixed list of motivations](https://www.w3.org/TR/annotation-model/#motivation-and-purpose). Scholars have indicated a requirement for different types of motivations. One solution would be to allow defining of sub-classes of motivations, e.g. specific forms of commenting, tagging or transcribing, so that they always maps to the fixed list.
- **Audience**: we probably need to use [audience](https://www.w3.org/TR/annotation-model/#intended-audience) for user and group permissions. The [Working Group suggests](https://github.com/w3c/web-annotation/issues/119) to use the `type` property and [schema.org's audience schema](http://schema.org/Audience). See also the [permission model discussion](https://github.com/marijnkoolen/rdfa-annotation-client/blob/master/discussion/handling-permissions.md) in this repository.

### Storing and Retrieving Resource Structure

**Registering complex resources**: based on earlier discussion, it makes sense for the client to check if the server knows about the structure of a resource that the client is annotating, and if the server doesn't, for the client to send the structural information of the resource and all it's subresources to register all their relationships. Currently, it seems like Alexandria only has an endpoint for registering individual subresources with an `isPartOf` relationship with a resource. When the resources is highly complex, this would require many API calls. An alternative is for the server to traverse all relationships of a complex resource and store each relationship along the traversal. This could be done using the same endpoint, or to have a separate endpoint for registering complex resources similar to the endpoint for registering [IIIF annotation lists](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/webannotation/WebAnnotation.html).

**Multiple parentage and collections**: [*subresources* in Alexandria are labelled explicitly as *subresources*, not as *resources*](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/resource/Anatomy.html). That is, they have a `sub` field, not a `ref` field. 

For retrieving resources at an arbitrary level this is not a problem. Each sub-resource is a resource in its own right, and the URI-requirement for a sub-resource is identical to one for a resource (http://alexandriaserver.aaa/resources/UUID) which makes it possible to create a sub-resource based on a sub-resource; Internally, `sub` and `ref` both map to `cargo`.

*This is a problem for registering resources as part of multiple collections and sub-resources as part of multiple resources. Currently the resource--sub-resource relationship in Alexandria is strictly hierarchical.*


**Identifiers and references**: Alexandria uses `uuid` as internal identifier for (sub)resources. The format of the `ref` and `sub` (i.e. `cargo`) fields is up to the user. For Web Annotations this must be an IRI. Alexandria allows multiple registrations of the same `ref` and doesn't check uniqueness of this field. 

*The RDFa-based annotation approach requires that resource identifiers are unique, but multiple contexts are possible (e.g. multiple editions containing the same resource but as part of different collections and with potentially different subsets of sub-resources.*

### Additional Resource Properties

What additional properties should Alexandria be able to store on a resource? 

- **resource type**: based on Annotatable Thing ontology. There is no property in the specification of the Web Annotation model to identify the target resource type. Should Alexandria use the ontology to verify the types and their relationships? Or should it trust the client or the edition to do this well? [BB: No Resource types defined currently]
- **media-type of the annotation target**: should the annotation server be aware of the media-type of a resource? E.g. for querying by media-type? Probably not, since Web Annotations allow [specifying media-type of an annotation target](https://www.w3.org/TR/annotation-model/#external-web-resources) (and body) via the `format` property. The general type of a resource can be [specified as a class on target](https://www.w3.org/TR/annotation-model/#classes) (and body) via the `type` property (i.e. *Data*, *Image*, *Sound*, *Text*, *Video*).


### Querying and Filtering

 Annotation client is always in context of one or a few resources (e.g. a list of resources in a search/browse results list). With resource ids as constraints, filtering is relatively straightforward. When the annotation client is loaded in a browser window, it sends a request to the server for annotations on resources that it observes. Users may wish to filter these annotations based on different aspects, such motivation/task type, motivation/task label, date, user, group, ...

Outside the annotation client, there may be additional requirements for querying the annotation server. The task of annotating is part of the larger research process. Later tasks that use these annotations include analytical steps whereby the researcher may want to aggregate or compare (selections of) annotations. 

In the context of the Van Gogh and Mondriaan use cases, a researcher may wish to query for annotations based on *creator*, *motivation*, *tag/code/classification label*, *creation date* or the *type of resource* that is targeted by annotation.

To get a broader view of future requirements for querying and filtering annotations, the proposals of the [CLARIAH WP5 research pilots](http://www.clariah.nl/projecten/research-pilots) have been analysed and a rough estimate of their annotation tasks and querying requirements are listed below:

- **DReAM**: cross-media analysis of trajectories of drugs and regulations
  - annotate mentions of drug components in broadcast media
  - query for annotations based on annotation bodies (types, values)

- **M&M**: trace emergence of a genre based on analysis of cues related to genre conventions
  - annotation of oral and visual cues in video (bottom-up coding?)
  - annotate video stream of TV broadcasts in combination with TV program guides
  - querying for free-form tags and batch-updating them with more controlled codes
  - querying codes in combination with resource metadata for analysis

- **CrossEWT**: historical development of eye-witness testimonies of WWII
  - manually annotate testimonies, use manual annotations to bootstrap automtatic recognition, extraction, annotation
  - query automatic annotations for manual verification

- **MIMEHIST**: annotate video stream of films in combination with film posters, photos and distribution data
  - querying annotations via bodies in combination with resource metadata 
  - querying annotations via creator, date and tags

- **NarDis**: analysing narrative constructing during exploratory search
  - exploring linked data collections, generating paths/trails of entities,  and generating narratives based on the relations between entities along the paths using annotations.
  - building trails of entities related to disruptive media events, annotate relations between entities, compare trails via annotations and entities
  - querying for annotations based on arbitrary sets of resources

This results in the following list of selection and filtering options:

- `GET` annotations by (a combination of):
	- **Annotation ID**
	- **Resource ID** (with or without annotations on sub-resources)
	- **Creator ID**

- Searching annotations by:
	- **Target resource type**: e.g. only annotations on `Transciption` type resources.
	- **Target text**: e.g. only annotations on text selections containing *cortex china*.
	- **Motivation/task type**: e.g. only `correction` annotations,
	- **Motivation/task label**: e.g. only `classify` annotations with the classification *colour*.
	- **Creation date range**: e.g. only annotations made today or in January 2017.
	- **Creator**: only annotations made by me or user X, or user X, Y and Z.
	- **Resource metadata**: e.g. resource creator, resource type, resource creation date, or any other metadata field and/or value of a resource.
	- **Permission group**: only annotations accessible by group Y (not sure how this information can/will be registered as part of annotations or in separate user and group DB).
	
The `GET` actions are currently possible in Alexandria, the filtering mentioned is not.