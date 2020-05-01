from flask import Flask, Blueprint, request, abort, make_response, jsonify, g, json
from flask_restx import Namespace, Resource, fields
from flask_restx import Api
from models.error import InvalidUsage
from models.annotation import AnnotationError

from .user import api as ns_user
from .annotation import api as ns_annotation
from .collection import api as ns_collection

blueprint = Blueprint('api', __name__)
api = Api(blueprint,
          title='CLARIAH Scholarly Web Annotation Server',
          version='1',
          description='RESTful API for Scholarly Web Annotations',
          doc='/doc'
          # All API metadatas
)

api.add_namespace(ns_user)
api.add_namespace(ns_annotation)
api.add_namespace(ns_collection)


@api.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    return error.to_dict(), error.status_code


@api.errorhandler(AnnotationError)
def handle_annotation_error(error):
    return error.to_dict(), error.status_code


# handled by Flask restplus api
@api.errorhandler
def handle_unauthorized_api(_error):
    # return 403 instead of 401 to prevent browsers from displaying the default auth dialog
    return {'message': 'Unauthorized access'}, 403


"""--------------- Annotation endpoints ------------------"""


# generic response model
response_model = api.model("Response", {
    "status": fields.String(description="Status", required=True, enum=["success", "error"]),
    "message": fields.String(description="Message from server", required=True),
})


@api.route("/", endpoint='api_base')
class BasicAPI(Resource):

    @api.response(200, 'Success', response_model)
    @api.response(400, 'API Error', response_model)
    def get(self):
        return {"message": "Annotation server online"}



