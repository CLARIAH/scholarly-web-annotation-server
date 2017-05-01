annotations = {
    "no_target": {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "motivation": "classifying",
        "body": [
            {
                "type": "Classifying",
                "value": "Vincent van Gogh",
                "vocabulary": "DBpedia",
                "id": "http://dbpedia.org/resource/Vincent_van_Gogh",
                "purpose": "classifying"
            }
        ]
    },
    "vincent": {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "target": [
            {
                "id": "urn:vangogh:testletter.sender",
                "type": "Sender",
                "conformsTo": "http://localhost:3000/vocabularies/vangoghontology.ttl#",
                "selector": None
            }
        ],
        "motivation": "classifying",
        "body": [
            {
                "type": "Classifying",
                "value": "Vincent van Gogh",
                "vocabulary": "DBpedia",
                "id": "http://dbpedia.org/resource/Vincent_van_Gogh",
                "purpose": "classifying"
            }
        ]
    },
    "theo": {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "target": [
            {
                "id": "urn:vangogh:testletter.receiver",
                "type": "Receiver",
                "conformsTo": "http://localhost:3000/vocabularies/vangoghontology.ttl#",
                "selector": None
            }
        ],
        "motivation": "classifying",
        "body": [
            {
                "type": "Classifying",
                "value": "Theo van Gogh (art dealer)",
                "vocabulary": "DBpedia",
                "id": "http://dbpedia.org/resource/Theo_van_Gogh_(art_dealer)",
                "purpose": "classifying"
            }
        ]
    },
    "brothers": {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "Annotation",
        "target": [
            {
                "id": "urn:vangogh:testletter.sender",
                "type": "Sender",
                "conformsTo": "http://localhost:3000/vocabularies/vangoghontology.ttl#",
                "selector": None
            }
        ],
        "motivation": "classifying",
        "body": [
            {
                "type": "Classifying",
                "value": "Brother",
                "vocabulary": "DBpedia",
                "id": "http://dbpedia.org/resource/Brother",
                "purpose": "classifying"
            }
        ]
    },
}

annotation_pages = [
    {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "AnnotationPage",
        "id": ""
    }
]

annotation_collections = {
    "empty_collection": {
        "@context": "http://www.w3.org/ns/anno.jsonld",
        "type": "AnnotationCollection",
        "label": "Some collection",
        "total": 0,
        "first": "urn:uuid:1dadd70a-f5ad-44d0-a1fb-882ffc994cfd",
        "last": "urn:uuid:1dadd70a-f5ad-44d0-a1fb-882ffc994cfd",
    }
}

