from flask import Blueprint
from flask_restplus import Api, Model, fields


blueprint = Blueprint('api', __name__)
api = Api(blueprint)

"""--------------- API request and response models ------------------"""

# generic response model
response_model = Model("Response", {
    "status": fields.String(description="Status", required=True, enum=["success", "error"]),
    "message": fields.String(description="Message from server", required=True),
})

# user created response model
user_response = Model("Response", {
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
        "created": {
            "type": "string",
            "format": "date-time"
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

annotation_model = Model("Annotation", {
    "@context": fields.String(description="The context that determines the meaning of the JSON as an Annotation",
                              required=True, enum=["http://www.w3.org/ns/anno.jsonld"]),
    "id": fields.String(description="Annotation ID", required=False),
    "type": fields.String(description="Annotation Type", required=True,
                          enum=["Annotation", "AnnotationPage", "AnnotationCollection"]),
    "creator": fields.String(description="Annotation Creator", required=False),
    "body": fields.List(fields.Nested(body_model))
})

annotation_response = Model.clone("AnnotationResponse", response_model, {"annotation": fields.Nested(annotation_model)})

annotation_list_response = Model.clone("AnnotationListResponse", response_model, {
    "annotations": fields.List(fields.Nested(annotation_model), description="List of annotations")
})


