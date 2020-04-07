# IIIF Annotations

This document describes the IIIF Presentation API as a potential vehicle for RDFa enriched multimedia resource description.

Table of Contents:

+ [Background](#background)
+ [IIIF Resource Representation](#iiif_representation)
+ [Resource Hierarchies as IIIF Collections and Manifests](#iiif_model)
+ [Existing IIIF Image Collection Examples](#iiif_examples)

<a name="background"></a>
## IIIF and Web Annotations

The [IIIF Presentation API (version 2.1)](http://iiif.io/api/presentation/2.1/) specifies how [Advanced Association Features](http://iiif.io/api/presentation/2.1/#advanced-association-features) can be incorporated as annotations based on the proposed [Open Annotation Model](http://www.openannotation.org/spec/core/), which has been superseded by the [Web Annotation Model](https://www.w3.org/TR/annotation-model/).

There is international interest to extend IIIF to IXIF to cover any media type. See this [blog post at the Netherlands Institute for Sound and Vision](https://www.beeldengeluid.nl/en/blogs/research-amp-development-en/201604/interweaving-online-media-ixif). Some first steps are described in a [gist by Tom Crane of the Wellcome library](https://gist.github.com/tomcrane/7f86ac08d3b009c8af7c). The Wellcome library also worked on the [Universal Viewer](https://universalviewer.io/), which supports IXIF "out of the box".

## IIIF Resource Structure: Manifests, Sequences, ...

This sections reviews [IIIF Presentation API section 5](http://iiif.io/api/presentation/2.1/#resource-structure) in the context of Web Annotations.

+ A `manifest` represents an object and one or more works (resources) embedded in that object. 
+ The `sequences` property can be used to describe the order of part's-of a work, i.e. sub-resources of a resource. Each part is represented by a `canvas`. There can be multiple `sequences`. A `manifest` `MUST` embed a single sequence, additional `sequences` should be linked via an `URI`. **A consequence of this approach is that a `manifest` can only represent a single layer of sub-resources. Multi-level hierarchies have to be represented through manifests of manifests.**
+ A `canvas` represents a single view (typically a page in IIIF context). It is a spatial (2D) concept and requires width and height. Images are connected to a `canvas` via *annotations* which `MUST` be indicated via a `motivation` with value `sc:painting` .  **Transcriptions of an image that are to be displayed `MUST` also use this same motivation. The reason is that it allows clients to determine elements are to be displayed as representations of a resource. Conceptually, this is very useful for separating annotations on a resource from annotations that indicate resource structure. **
+ A `canvas` may contain non-image content (such as transcriptions, video/audio links) as annotations in an `oa:AnnotationList` via the `otherContent` property.
+ An `Annotation List` contains annotations on an object and can (I think) be a mix of non-image representations of the object (via the `motivation: sc:painting`) and comments, i.e. annotations *on* the object.
+ A `range` is used to represented other, overlapping, structure of the object. A typical example in IIIF context is the overlapping hierarchies represented by page structure and logical structure (chapters, sections, articles) in a book or newspaper. The `members` property will probably be the only property to express membership, as `ranges` and `canvases` are likely to be deprecated in version 3.0 (see [section 5.6](http://iiif.io/api/presentation/2.1/#range)).
+ The `structures` property represents additional structural information in the form of `Range`s.
+ A `layer` represents a grouping of annotation lists (similar to groupings of annotation tiers in e.g. [ELAN](https://tla.mpi.nl/tools/tla-tools/elan/)?). Annotation lists can be part of multiple layers, so layers and annotation lists are many-to-many relations. 
+ A `collection` combines multiple manifests. **"Collection are used to list the manifests available for viewing, and to describe the structures, hierarchies or curated collections that the physical objects are part of. The collections may include both other collections and manifests, in order to form a hierarchy of objects with manifests at the leaf nodes of the tree."** ([IIIF Presentaiton API Section 5.8](http://iiif.io/api/presentation/2.1/#collection))

Discussion:

+ Marijn: perhaps we can use the `manifest` concept as inspiration for representing resource structure (relations between a resource and its sub-resources).

<a name="iiif_model"></a>
## Resource Hierarchies as IIIF Collections and Manifests

Below is an attempt to model the structure of a van Gogh letter in representations of IIIF collections and manifests.

#### The whole letter as collection:
```json
{
  "@context": [
    "http://iiif.io/api/presentation/2/context.json",
    "http://wellcomelibrary.org/ixif/0/context.json"
  ],
  "@id": "urn:vangogh:letter001.collection",
  "@type": "sc:Collection",
  "label": "Letter Level Collection for Van Gogh letter",
  "viewingHint": "top",
  "description": "Description of Letter",
  "attribution": "Provided by Huygens/ING",

  "members": [
    {
      "@id": "urn:vangogh:letter001:sender.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Sender manifest",
    },
    {
      "@id": "urn:vangogh:letter001:receiver.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Receiver manifest",
    },
    {
      "@id": "urn:vangogh:letter001:date.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Date manifest",
    },
    {
      "@id": "urn:vangogh:letter001:p:1.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 ParagraphInLetter 1 manifest",
    },
    {
      "@id": "urn:vangogh:letter001:trans.collection",
      "@type": "sc:Collection",
      "label": "Letter 001 Translation collection",
    },
  ]
}
```

**Note**:

+ There are two contexts, one for properties borrowed from IIIF, one for properties taken from the draft IXIF model.

#### The sender as manifest:

```json
{
  "@context": [
    "http://iiif.io/api/presentation/2/context.json",
    "http://wellcomelibrary.org/ixif/0/context.json"
  ],
  "@id": "urn:vangogh:letter001:sender.manifest",
  "@type": "sc:Manifest",
  "label": "Sender Level Manifest for Van Gogh letter 001",
  "viewingHint": "top",
  "description": "Description of Sender",
  "attribution": "Provided by Huygens/ING",
  "metadata": [
    { "label": "type", "value": "Sender" },
    { "label": "property", "value": "hasMetadataItem" }
  ],
  "mediaSequences": [
    {
      "@id": "urn:vangogh:letter001:sender.sequence",
      "type": "ixif:mediaSequence",
      "label": "Letter 001 Sender sequence"
      "elements": [
        {
          "@id": "urn:vangogh:letter001.sender",
          "type": "vg:Sender",
          "label": "Letter 001 Sender"
        }
      ]
    }
  ],
  "sequences": [
  {
    "@id": "http://wellcomelibrary.org/iiif/ixif-message/sequence/seq",
    "@type": "sc:Sequence",
    "label": "Unsupported extension. This manifest is being used as a wrapper for non-IIIF content (e.g., audio, video) and is unfortunately incompatible with IIIF viewers.",
    "compatibilityHint": "displayIfContentUnsupported",
    "canvases": [
      {
        //... a placeholder image for other viewers to look at...
      }
    ]
  }
}
```

**Note**: 

+ the `sequence` property is used by viewers to determine which sequences represent image view. We shouldn't reuse `sequence` for other purposes because in the IIIF model, that has the explicit semantics of "coherent sequence of images". There current placeholder and hint as suggested by Tom Crane, so that image viewers have something to display.
+ the `mediaSequence` is not part of IIIF but a proposed IXIF property. It is used to represent media objects that are not (necessarily) images.


#### The translation as sub-collection:

```json
{
  "@context": [
    "http://iiif.io/api/presentation/2/context.json",
    "http://wellcomelibrary.org/ixif/0/context.json"
  ],
  "@id": "urn:vangogh:letter001:trans.collection",
  "@type": "sc:Collection",
  "label": "Translation Level Collection for Van Gogh letter 001",
  "viewingHint": "top",
  "description": "Description of Translation of van Gogh Letter 001",
  "attribution": "Provided by Huygens/ING",

  "members": [
    {
      "@id": "urn:vangogh:letter001:trans:p1.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Translation Paragraph 1 manifest",
    },
    {
      "@id": "urn:vangogh:letter001:trans:p2.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Translation Paragraph 2 manifest",    },
    {
      "@id": "urn:vangogh:letter001:trans:p3.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Translation Paragraph 3 manifest",    },
    {
      "@id": "urn:vangogh:letter001:trans:p4.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Translation Paragraph 4 manifest",    },
    {
      "@id": "urn:vangogh:letter001:trans:p5.manifest",
      "@type": "sc:Manifest",
      "label": "Letter 001 Translation Paragraph 5 manifest",    },
  ]
} 
```

## Advanced Association Features

The IIIF Presentation API further allows incorporation of annotations based on the W3C Web Annotation framework:

+ The W3C Web Annotation model uses the <code>https://www.w3.org/ns/anno.jsonld</code> context.
+ The IIIF model uses the <code>http://iiif.io/api/presentation/2/context.json</code> context. 
+ the annotation target is a canvas, the body is an image.
+ the annotation target is referred to by the `on` property in  IIIF, `target` in the Web Annotation model. Through their respective `@context`s, they both map to `oa:hasTarget` (see [Web Annotation Ontology](https://www.w3.org/ns/oa#)).
+ the annotation body is referred to by the `resource` property in IIIF, `body` in the Web Annotation model. Through their respective `@context`s, they both map to `oa:hasBody` (see [Web Annotation Ontology](https://www.w3.org/ns/oa#)).
+ [Segment selection](http://iiif.io/api/presentation/2.1/#segments) in a canvas is represented as an annotation.
+ Textual annotations can be incorporated as [Embedded content](http://iiif.io/api/presentation/2.1/#embedded-content) using RDF Content Representation. 

<a name="iiif_examples"></a>
## Existing IIIF Image Collection Examples

#### Example from e-codices

Collection of collections:
> http://www.e-codices.unifr.ch/metadata/iiif/collection.json

Collection of manifests (the collection of manifests of Einsiedeln, Stiftsbibliothek):
> http://www.e-codices.unifr.ch/metadata/iiif/collection/sbe.json

Manifest (codex 109 in collection of Einsiedeln, Stiftsbibliothek):
> http://www.e-codices.unifr.ch/metadata/iiif/sbe-0109/manifest.json

#### Example from the British Library
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
