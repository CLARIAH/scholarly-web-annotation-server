# Proposal for a new nested resource selector

The annotation server should be able to fetch all annotations that target a resource or one of its subresources, including annotations on top of an annotation that targets the (sub)resource, whereby each (sub)resource has its own `id` and the annotations adhere to the [W3C Web Annotation data model](https://www.w3.org/TR/annotation-model/). Conceptually, the resources and annotations form a (directed acyclic) graph. There are two ways to communicate between client and server:

1. annotations only contain information on the specific (sub)resource they target. Information about how resources and subresources are related to each other is submitted to the server separately. The server keep track of the resource structure information in a separate index.
2. the information on resource structure is stored in each annotation, so the `target` field of an annotation contains a branch from resource to the most specific subresource of that resource that is targeted.  

The latter results in more replication of information (all annotations on the same subresource of a document contain the full path from the document to the subresource), but has the advantages that individual annotations are easier to interpret out of context, as they are more verbose, and that the server is easier to understand, as the only objects that are exchanged are annotations.

To make this possible, a new type of selector is needed that can store a nested resource structure information.

As an example, consider a digital edition of a letter written by Vincent Van Gogh, with an annotation targeting a fragment of the first paragraph of a translated version of that letter. A second annotation targets the first annotation. When the client ask for all annotations of either 1) the letter, 2) the translated version, or 3) the first paragraph of the translated version, the server should return both annotations. 

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

Below is an example of a full annotation using these two selectors as alternatives of each other:

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
								"id": "urn:vangogh:testletter:translation:p.1",
								"type": ["Paragraphinletter", "Text"],
								"property": "hasPart"
							}
						}
					}
				},
				"refinedBy": {
					"type": "TextPositionSelector",
					"start": 76,
					"end": 86
				}
			}
		]
	}
}

```

## Indexing in Elasticsearch

Requirements:

1. fetch all annotations targeting:
    - 1a. specific resource or one of its subresources, 
    - 1b. and annotations on those annotations.
2. when updating one annotation, other annotations that target that annotation should be updated where necessary.

**Note: neither of the two proposed selectors above meet requirement 1b. An annotation *a_1* that targets another annotation *a_2* does not contain information about the resources that *a_2* targets, so will not directly match requests for annotations on the targets of *a_1*.**

Requirement 1b can be fulfilled by adding a `target_list` field in the annotation upon indexing that annotation, and adding the `id`s of all (sub)resource targets of the annotation itself to the `target_list`, as well as of all annotations that it targets and their (sub)resource targets. The `target_list` field is removed by the server when passing the annotation to a client. That is, the `target_list` is only used internally for retrieval. 

The full example annotation above will have the following `target_list`:

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

An annotation that target the full example annotation will have the following `target_list`:

```json
{
    "target_list": [
    	{
	    "id": "urn:uuid:6273d09b-0ec2-4d90-955b-90aeece1aecd",
	    "type": ["Annotation"]
	},
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

To be more context-independent, the `target_list` can contain not only the `id` but also `type` and `property` information of each (sub)resource and annotation, so that annotations can be retrieved for specific resources as well as for specific resource types.

**Note that if the example annotation is updated with a different list of targets, the `target_list` fields of both annotations need to be updated.**
