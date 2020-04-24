from flask import Blueprint
from flask_restplus import Api, Model, fields


blueprint = Blueprint('api', __name__)
api = Api(blueprint)

"""--------------- API request and response models ------------------"""

# generic response model
response_model = api.model("Response", {
    "status": fields.String(description="Status", required=True, enum=["success", "error"]),
    "message": fields.String(description="Message from server", required=True),
})

# user created response model
user_response = api.model("UserResponse", {
    "action": fields.String(descrption="Update action", require=True,
                            enum=["created", "verified", "updated", "deleted"]),
    "user": {
        "username": fields.String(description="Username", required=True)
    }
})

target_model = api.schema_model("AnnotationTarget", {
    "properties": {
        "id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        },
        "language": {
            "type": "string"
        },
    }
})

body_model = api.schema_model("AnnotationBody", {
    "properties": {
        "id": {
            "type": "string"
        },
        "type": {
            "type": "string"
        },
        "purpose": {
            "type": "string"
        },
        "value": {
            "type": "string"
        },
    },
    "type": "object"
})

new_annotation_model = api.model("NewAnnotation", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    "creator": fields.String(description="Annotation Creator", required=False),
    "body": fields.List(fields.Nested(body_model)),
    "target": fields.List(fields.Nested(target_model))
})

annotation_model = api.model("Annotation", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "id": fields.String(description="Annotation ID", required=False),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    "creator": fields.String(description="Annotation Creator", required=False),
    "created": fields.DateTime(description='Annotation created timestamp', required=False),
    "body": fields.List(fields.Nested(body_model)),
    "target": fields.List(fields.Nested(target_model))
})

annotation_response = api.clone("AnnotationResponse", response_model, {"annotation": fields.Nested(annotation_model)})

annotation_list_response = api.clone("AnnotationListResponse", response_model, {
    "annotations": fields.List(fields.Nested(annotation_model), description="List of annotations")
})
