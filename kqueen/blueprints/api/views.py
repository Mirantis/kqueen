from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request
from flask_jwt import jwt_required
from kqueen.models import Cluster
from kqueen.models import Provisioner
from uuid import UUID

import logging
import json

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

def get_obj(_class, pk):
    # read uuid
    try:
        object_id = UUID(pk, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = _class.load(object_id)
    except NameError:
        abort(404)

    return obj


# TODO: use <resource>
@api.route('/clusters', methods=['GET'])
@jwt_required()
def cluster_list():
    # TODO: implement native serialization

    output = []

    for cluster in list(Cluster.list(return_objects=True).values()):
        output.append(cluster.get_dict())

    return jsonify(output)


@api.route('/clusters', methods=['POST'])
@jwt_required()
def cluster_create():
    if not request.json:
        abort(400)
    else:
        obj = Cluster(**request.json)
        try:
            obj.save()
            output = obj.serialize()
        except:
            abort(500)

    return jsonify(output)


@api.route('/clusters/<pk>', methods=['GET'])
@jwt_required()
def cluster_get(pk):
    obj = get_obj(Cluster, pk)

    return jsonify(obj.get_dict())


@api.route('/clusters/<pk>', methods=['PATCH'])
@jwt_required()
def cluster_update(pk):
    if not request.json:
        abort(400)

    data = json.load(request.json)
    if not isinstance(data, dict):
        abort(400)

    obj = get_obj(Cluster, pk)
    for key, value in data.items():
        print(key, value)




@api.route('/clusters/<pk>', methods=['DELETE'])
@jwt_required()
def cluster_delete(pk):
    obj = get_obj(pk)

    try:
        obj.delete()
    except:
        abort(500)


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


# Provisioners

@api.route('/provisioners', methods=['GET', 'POST'])
@jwt_required()
def provisioner_list():
    # TODO: implement native serialization

    if request.method == 'POST':
        if not request.json:
            abort(400)
        else:
            try:
                raise NotImplementedError
            except:
                abort(500)

    else:
        output = []

        for obj in list(Provisioner.list(return_objects=True).values()):
            output.append(obj.get_dict())

    return jsonify(output)


@api.route('/provisioners/<provisioner_id>', methods=['GET'])
@jwt_required()
def provisioner_detail(provisioner_id):

    # read uuid
    try:
        object_id = UUID(provisioner_id, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = Provisioner.load(object_id)
    except NameError:
        abort(404)

    return jsonify(obj.get_dict())
