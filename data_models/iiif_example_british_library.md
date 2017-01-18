# IIIF Annotations

Below is an example of an annotation in [IIIF](http://iiif.io/) format, taken from the British Library ([source](http://sanddragon.bl.uk/IIIFMetadataService/Cotton_MS_Claudius_B_IV.json)). Note that the annotation target is a canvas&mdash;referred to by the property `on`&mdash;and the `resource` property refers to the annotation body, which in this case is an image. 

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