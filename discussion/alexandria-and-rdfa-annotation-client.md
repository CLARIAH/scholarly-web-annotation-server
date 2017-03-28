# Alexandria and RDFa-based Web Annotation

The purpose of this document is to analyse the gap between Alexandria and the RDFa Annotation Client. [Alexandria](http://huygensing.github.io/alexandria/) is a text repository and annotation server. The RDFa Annotation Client adopts a new approach to annotations that Alexandria was not designed for. If we want to use Alexandria as the annotation server to support the client and this approach, adjustments have to be made to Alexandria to fit the requirements. 


### W3C Web Annotation Model

The client sends and accepts annotations that are in the format of the [W3C Web Annotation Model](https://www.w3.org/TR/annotation-model/#annotations). Currently, Alexandria only implements a part of this standard, namely, to [support IIIF annotation lists](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/webannotation/WebAnnotation.html).

How much of the Web Annotation model is needed for the RDFa annotation approach?

### Storing and Retrieving Resource Structure

- multiple parentage and registering resources as part of multiple collections: [*subresources* in Alexandria are labelled explicitly as *subresources*, not as *resources*](http://huygensing.github.io/alexandria/alexandria-acceptance-tests/concordion/nl/knaw/huygens/alexandria/resource/Anatomy.html). That is, they have a `sub` field, not a `ref` field. 
- identifiers and references: Alexandria uses `uuid` as internal identifier for (sub)resources. What are the requirements for the `ref` field? Should it be an URI or an URL?

### Additional Resource Properties

What additional properties should Alexandria be able to store on a resource? 

- resource type: based on Annotatable Thing ontology. There is no property in the specification of the Web Annotation model to identify the target resource type.
- annotation target media-type: should the annotation server be aware of the media-type of a resource? E.g. for querying by media-type? Probably not, since Web Annotations allow specifying media-type of an annotation target (and body) via the `format` property. The general type of a resource can be specified on target (and body) via the `type` property (i.e. *Data*, *Image*, *Sound*, *Text*, *Video*).


