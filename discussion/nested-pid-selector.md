# Proposal for a new nested resource selector

The annotation server should be able to fetch all annotations that target a resource or one of its subresources. Either the annotation only contains information on the specific (sub)resource it targets, and there is a separate index in the server to keep track of how resources and subresources are related to each other, or the information on resource structure is stored in each annotation. 

The latter results in more replication of information (all annotations on a subsubresource of a document contain the full path from the document to the subsubresource), but has the advantages that individual annotations are easier to interpret out of context and that the server is easier to understand, as it only has an annotation index.

To make this possible, a new type of selector is needed that can store a nested resource structure information.

## Selector proposals

Jaap Blom proposed a new type of selector to take care of this, called a NestedPIDSelector. All ancestors of the most specifically targeted resource are listed, from largest resources to smallest subresource. So order has meaning in a NestedPIDSelector.

Example:

```
"target": {
    "source": "urn:vangogh:testletter",
    "type": "Letter",
    "selector": {
        "type": "NestedPIDSelector",
        "value": [
            {
                "id": "urn:vangogh:correspondence",
                "type": ["Correspondence"],
                "property": "isPartOf"
            },
            {
                "id": "urn:vangogh:testletter",
                "type": ["Letter"],
                "property": "hasPart"
            },
            {
                "id": "urn:vangogh:testletter.translation",
                "type": "Translation",
                "property": "hasTranslation"
            },
            {
                "id": "urn:vangogh:testletter:translation:p.1",
                "type": ["Paragraphinletter", "Text"],
                "property": "hasPart"
            }
        ],
        "refinedBy": {
            "type": "TextPositionSelector",
            "start": 76,
            "end": 86
        }
    }
}
```

To select a fragment of the deepest PID, a `refinedBy` selector is added. **Note**: the source identifier is the `Letter` which is the context in which the annotation is made. However, within that context, the RDFa information indicates that the `Letter` is part of a `Correspondence`, therefor, the nested PIDs start from the larger Correspondence.

A more explicit alternative would be a `SubresourceSelector` that nests all subresources, again, starting from the larger `Correspondence`. 

```
"target": {
    "source": "urn:vangogh:testletter",
    "type": "Letter",
    "selector": {
        "type": "SubresourceSelector",
        "value": {
            "id": "urn:vangogh:correspondence",
            "type": ["Correspondence"],
            "subresource": {
                "id": "urn:vangogh:testletter",
                "type": ["Letter"],
                "property": "hasPart",
                "subresource": {
                    "id": "urn:vangogh:testletter.translation",
                    "type": "Translation",
                    "property": "hasTranslation",
                    "subresource": {
                        "id": "urn:vangogh:testletter:translation:p.1",
                        "type": ["Paragraphinletter", "Text"],
                        "property": "hasPart"
                    }
                }
            },
        }
        "refinedBy": {
            "type": "TextPositionSelector",
            "start": 76,
            "end": 86
        }
    }
}
```

Below is an example of a full annotation using these two selectors as alternatives:

```json
{
	"@context": "http://www.w3.org/ns/anno.jsonld",
	"type": "Annotation",
	"id": "urn:uuid:6273d09b-0ec2-4d90-955b-90aeece1aecd",
	"creator": "me",
	"created": "2017-05-10T08:50:49.055950+00:00",
	"body": [
		{
			"value": "Oisterwijk",
			"type": "Text",
			"purpose": "classifying",
			"id": "http://dbpedia.org/resource/Oisterwijk",
			"vocabulary": "DBpedia"
		}
	],
	"target": {
		"source": "urn:vangogh:testletter",
		"type": "Letter",
		"selector": [
			{
				"type": "NestedPIDSelector",
				"value": [
					{
						"id": "urn:vangogh:correspondence",
						"type": ["Correspondence"],
						"property": "isPartOf"
					},
					{
						"id": "urn:vangogh:testletter",
						"type": ["Letter"],
						"property": "hasPart"
					},
					{
						"id": "urn:vangogh:testletter.translation",
						"type": "Translation",
						"property": "hasTranslation"
					},
					{
						"id": "urn:vangogh:testletter:translation:p.1",
						"type": ["Paragraphinletter", "Text"],
						"property": "hasPart"
					}
				],
				"refinedBy": {
					"type": "TextPositionSelector",
					"start": 76,
					"end": 86
				}
			},
			{
				"type": "SubresourceSelector",
				"value": {
					"id": "urn:vangogh:correspondence",
					"type": ["Correspondence"],
					"subresource": {
						"id": "urn:vangogh:testletter",
						"type": ["Letter"],
						"property": "hasPart",
						"subresource": {
							"id": "urn:vangogh:testletter.translation",
							"type": "Translation",
							"property": "hasTranslation",
							"subresource": {
								"id": "urn:vangogh:testletter:translation:p.5",
								"type": ["Paragraphinletter", "Text"],
								"property": "hasPart"
							}
						}
					}
				}
				"refinedBy": {
					"type": "TextPositionSelector",
					"start": 76,
					"end": 86
				}
			}
		]
	}
]

```

## Indexing in Elasticsearch

Requirements:

1. fetch all annotations targeting:
    - 1a. specific resource or one of its subresources, 
    - 1b. and annotations on those annotations.
2. when updating one annotations, ensure annotations on that annotation are updated where necessary.

Requirement 1 is achiedved by adding a `target_list` field in the annotation upon indexing that annotation. The `target_list` field is removed by the server when passing the annotation to a client. That is, the `target_list` is only used internally for retrieval. 

**Note that the target list also contains a list of resources for annotations on annotations, therefore, is more powerful than the NestedPIDSelector.** An annnotation that targets the annotation example above has a target list that includes the example annotation as well as the path of (sub)resources that the example annotation targets. **The NestedPIDSelector does not meet requirement 1b.**

The target list contains both `id` and `type` information of each (sub)resource, so that annotations can be retrieved for specific resources as well as resource types.

```json
{
    "target_list": [
        {
            "id": "urn:vangogh:correspondence",
            "type": ["Correspondence"],
        },
        {
            "id": "urn:vangogh:testletter",
            "type": ["Letter"],
        },
        {
            "id": "urn:vangogh:testletter.translation",
            "type": "Translation",
        },
        {
            "id": "urn:vangogh:testletter:translation:p.1",
            "type": ["Paragraphinletter", "Text"],
        }
    ]
}
```

