# IIIF Annotations

Below is an example of an annotation in [IIIF](http://iiif.io/) format, taken from the British Library ([source](http://sanddragon.bl.uk/IIIFMetadataService/Cotton_MS_Claudius_B_IV.json)). 

Note that there are some differences between the IIIF Presentation API and the W3C Web Annotation framework:

+ the annotation target is a canvas, the body is an image. 
+ the annotation target is referred to by the `on` property in  IIIF, `target` in the Web Annotation model.
+  the annotation body is referred to by the `resource` property in IIIF, `body` in the Web Annotation model.

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