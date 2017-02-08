# IIIF Annotations

## IIIF and Web Annotations

The [IIIF Presentation API (version 2.1)](http://iiif.io/api/presentation/2.1/) specifies how [Advanced Association Features](http://iiif.io/api/presentation/2.1/#advanced-association-features) can be incorporated as annotations based on the proposed [Open Annotation Model](http://www.openannotation.org/spec/core/), which has been superseded by the [Web Annotation Model](https://www.w3.org/TR/annotation-model/).

Note that there are some differences between the IIIF Presentation API and the W3C Web Annotation framework:

+ The W3C Web Annotation model uses the <code>https://www.w3.org/ns/anno.jsonld</code> context.
+ The IIIF model uses the <code>http://iiif.io/api/presentation/2/context.json</code> context. 
+ the annotation target is a canvas, the body is an image.
+ the annotation target is referred to by the `on` property in  IIIF, `target` in the Web Annotation model. Through their respective `@context`s, they both map to `oa:hasTarget` (see [Web Annotation Ontology](https://www.w3.org/ns/oa#)).
+ the annotation body is referred to by the `resource` property in IIIF, `body` in the Web Annotation model. Through their respective `@context`s, they both map to `oa:hasBody` (see [Web Annotation Ontology](https://www.w3.org/ns/oa#)).
+ [Segment selection](http://iiif.io/api/presentation/2.1/#segments) in a canvas is represented as an annotation.
+ Textual annotations can be incorporated as [Embedded content](http://iiif.io/api/presentation/2.1/#embedded-content) using RDF Content Representation. 
+ It is not clear whether annotations in IIIF can be nested. E.g. whether a textual annotation on a segment selection of an image requires two annotations or can be nested in a single annotation. 

## IIIF Resource Structure: Manifests, Sequences, ...

+ A `manifest` represents an object and one or more works (resources) embedded in that object. 
+ The `sequences` property can be used to describe the order of part's-of a work, i.e. sub-resources of a resource. Each part is represented by a `canvas`. There can be multiple `sequences`. A `manifest` `MUST` embed a single sequence, additional `sequences` should be linked via an `URI`. A consequence of this approach is that a `manifest` can only represent a single `layer` of sub-resources.
+ A `canvas` represents a single view (typically a page in IIIF context). It is a spatial (2D) concept and requires width and height. A `canvas` may contain non-image content (such as transcriptions, video/audio links) as annotations in an `oa:AnnotationList`.
+ The `structures` property represents additional structural information in the form of `Range`s.

Discussion:

+ Marijn: perhaps we can use the `manifest` concept as inspiration for representing resource structure (relations between a resource and its sub-resources).

## Example from the British Library
Below is an example of an annotation in [IIIF](http://iiif.io/) format, taken from the British Library ([source](http://sanddragon.bl.uk/IIIFMetadataService/Cotton_MS_Claudius_B_IV.json)).

More details are available in the [IIIF Presentation API specification](http://iiif.io/api/presentation/2.0/).

```json
{
	"@id": "http://sanddragon.bl.uk/IIIFImageService/cotton_ms_clab4_f001r/imageanno/anno-1",
	"@type": "oa:Annotation",
	"motivation": "sc:painting",
	"resource": {
		"@id": "http://sanddragon.bl.uk/IIIFImageService/cotton_ms_clab4_f001r",
		"@type": "dctypes:Image",
		"tile_width": 256,
		"tile_height": 256,
		"height": 5861,
		"width": 4634,
		"service": {
			"@id": "http://sanddragon.bl.uk/IIIFImageService/cotton_ms_clab4_f001r",
			"profile": "http://library.stanford.edu/iiif/image-api/1.1/conformance.html#level1"
		}
	},
    "on": "http://sanddragon.bl.uk/IIIFImageService/cotton_ms_clab4_f001r/canvas/canvas-1"
}
```

The IIIF protocol for [Image Resources](http://iiif.io/api/presentation/2.0/#image-resources) allows inclusion of properties from the [W3C Web Annotation framework](https://www.w3.org/TR/annotation-model/).
