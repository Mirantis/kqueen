from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request
from flask_jwt import jwt_required
from kqueen.models import Cluster
from uuid import UUID

import logging

logger = logging.getLogger(__name__)

api = Blueprint('api', __name__)


# error handlers
def error_response(code, error):
    """Return JSONed response of error code.

    Attributes:
        code (int): Error code number.
        error (obj): HTTP error code

    Returns:
        JSONified error response
    """

    response = {'code': code, 'description': error.description}
    return make_response(jsonify(response), code)


@api.errorhandler(400)
def bad_request(error):
    return error_response(400, error)


@api.errorhandler(403)
def forbidden(error):
    return error_response(403, error)


@api.errorhandler(404)
def not_found(error):
    return error_response(404, error)


@api.errorhandler(500)
def not_implemented(error):
    return error_response(500, error)


@api.route('/')
@api.route('/health')
def index():
    return jsonify({'response': 'Gutten tag!'})


# Clusters
@api.route('/clusters', methods=['GET', 'POST'])
@jwt_required()
def cluster_list():
    # TODO: implement native serialization

    if request.method == 'POST':
        if not request.json:
            abort(400)
        else:
            obj = Cluster(**request.json)
            try:
                obj.save()
                output = obj.serialize()
            except:
                abort(500)

    else:
        output = []

        for cluster in list(Cluster.list(return_objects=True).values()):
            output.append(cluster.get_dict())

    return jsonify(output)


@api.route('/clusters/<cluster_id>', methods=['GET'])
@jwt_required()
def cluster_detail(cluster_id):

    # read uuid
    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = Cluster.load(object_id)
    except NameError:
        abort(404)

    return jsonify(obj.get_dict())


@api.route('/clusters/<cluster_id>/status', methods=['GET'])
@jwt_required()
def cluster_status(cluster_id):
    print(cluster_id)

    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = Cluster.load(object_id)
    except NameError:
        abort(404)

    return jsonify(obj.status())


@api.route('/clusters/<cluster_id>/topology-data', methods=['GET'])
def cluster_topology_data(cluster_id):

    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = Cluster.load(object_id)
    except NameError:
        abort(404)

    return jsonify(obj.topology_data())


@api.route('/clusters/<cluster_id>/kubeconfig', methods=['GET'])
@jwt_required()
def cluster_kubeconfig(cluster_id):

    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = Cluster.load(object_id)
    except NameError:
        abort(404)

    return jsonify(obj.kubeconfig)
