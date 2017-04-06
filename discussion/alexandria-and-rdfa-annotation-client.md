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

- **registering complex resources**: based on earlier discussion, it makes sense for the client to check if the server knows about the structure of a resource that the client is annotating, and if the server doesn't, for the client to send the structural information of the resource and all it's subresources to register all their relationships. Currently, it seems like Alexandria only has an endpoint for registering individual subresources with an `isPartOf` relationship with a resource. When the resources is highly complex, this would require many API calls. An alternative is for the server to traverse all relationships of a complex resource and store each relationship along the traversal. This could be done using the same endpoint, or to have a separate endpoint for registering complex resources.
- **multiple parentage and collections**: [*subresources* in Alexandria are labelled explicitly as *subresources*, not as *resources*](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/resource/Anatomy.html). That is, they have a `sub` field, not a `ref` field. This is a problem for 
	- registering resources as part of multiple collections and subresources as part of multiple resources. 
	- retrieving resources at an arbitrary level. Each sub-resource is a resource in its own right.
- **identifiers and references**: Alexandria uses `uuid` as internal identifier for (sub)resources. What are the requirements for the `ref` field? Should it be an URI or an URL? Must the value in the `ref` field be unique? That is, can a resource identified by a URI only be registered once?

### Additional Resource Properties

What additional properties should Alexandria be able to store on a resource? 

- **resource type**: based on Annotatable Thing ontology. There is no property in the specification of the Web Annotation model to identify the target resource type. Should Alexandria use the ontology to verify the types and their relationships? Or should it trust the client to do this well? 
- **media-type of the annotation target**: should the annotation server be aware of the media-type of a resource? E.g. for querying by media-type? Probably not, since Web Annotations allow [specifying media-type of an annotation target](https://www.w3.org/TR/annotation-model/#external-web-resources) (and body) via the `format` property. The general type of a resource can be [specified as a class on target](https://www.w3.org/TR/annotation-model/#classes) (and body) via the `type` property (i.e. *Data*, *Image*, *Sound*, *Text*, *Video*).


### Querying and Filtering

**Note 2017-04-05**: this section is definitely not yet finished. 

Upon loading the client, it sends a request to the server for annotations on resources that it observes. Beyond that, users of annotations may wish to filter annotations based on different aspects, such motivation/task type, motivation/task label, date, user, group, ...

- `GET` annotations by:
	- **annotation ID**
	- **resource ID** (with or without annotations on sub-resources)
	- **creator**
- `filter` annotations by:
	- **target resource type**: e.g. only annotations on `Transciption` type resources,
	- **target text**: e.g. only annotations on text selections containing *cortex china*,
	- **motivation/task type**: e.g. only `correction` annotations,
	- **motivation/task label**: e.g. only `classify` annotations with the classification *colour*,
	- **creation date range**: e.g. only annotations made today or in January 2017,
	- **creator**: only annotations made by me or user X,
	- **permission group**: only annotations accessible by group Y (not sure how this information can/will be registered as part of annotations or in separate user and group DB).
