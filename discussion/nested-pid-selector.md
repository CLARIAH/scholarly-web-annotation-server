# Proposal for a new NestedPIDSelector

Jaap Blom proposed a new type of selector to take care of this, called a NestedPIDSelector. All ancestors of the most specifically targeted resource are listed, from largest resources to smallest subresource. So order has meaning in a NestedPIDSelector.

Example:

```
“target”: {
    "source": "urn:vangogh:testletter",
    "type": "Letter",
    "selector": {
        "type": "NestedPIDSelector",
        "value": [
            {
                "id": "urn:vangogh:correspondence",
                "type": ["Correspondence"],
                “property”: “isPartOf”
            },
            {
                "id": "urn:vangogh:testletter",
                "type": ["Letter"],
                “property”: “hasPart”
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
        “refinedBy”: {
            “type”: “TextPositionSelector”,
            “start”: 76,
            “end”: 86
        }
    }
}
```

To select a fragment of the deepest PID, a `refinedBy` selector is added. **Note**: the source identifier is the `Letter` which is the context in which the annotation is made. However, within that context, the RDFa information indicates that the `Letter` is part of a `Correspondence`, therefor, the nested PIDs start from the larger Correspondence.

A more explicit alternative would be a `SubresourceSelector` that nests all subresources, again, starting from the larger `Correspondence`. 

```
“target”: {
    "source": "urn:vangogh:testletter",
    "type": "Letter",
    "selector": {
        "type": "SubresourceSelector",
        "value": {
            "id": "urn:vangogh:correspondence",
            "type": ["Correspondence"],
            “subresource”: {
                "id": "urn:vangogh:testletter",
                "type": ["Letter"],
                “property”: “hasPart”,
                “subresource”: {
                    "id": "urn:vangogh:testletter.translation",
                    "type": "Translation",
                    "property": "hasTranslation",
                    “subresource”: {
                        "id": "urn:vangogh:testletter:translation:p.1",
                        "type": ["Paragraphinletter", "Text"],
                        "property": "hasPart"
                    }
                }
            },
        }
        “refinedBy”: {
            “type”: “TextPositionSelector”,
            “start”: 76,
            “end”: 86
        }
    }
}
```

