from .helpers import get_object
from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request
from flask_jwt import jwt_required
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User

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

@api.route('/clusters', methods=['GET'])
@jwt_required()
def cluster_list():
    output = []

    for obj in list(Cluster.list(return_objects=True).values()):
        output.append(obj.get_dict())

    return jsonify(output)


@api.route('/clusters', methods=['POST'])
@jwt_required()
def cluster_create():
    if not request.json:
        abort(400)
    else:
        obj = Cluster(**request.json)
        try:
            # save cluster
            obj.save()
            output = obj.get_dict(expand=True)

            # start provisioning
            obj.engine.provision()

        except Exception as e:
            logger.error(e)
            abort(500)

    return jsonify(output)


@api.route('/clusters/<pk>', methods=['GET'])
@jwt_required()
def cluster_get(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/clusters/<pk>', methods=['PATCH'])
@jwt_required()
def cluster_update(pk):
    if not request.json:
        abort(400)

    data = request.json
    if not isinstance(data, dict):
        abort(400)

    obj = get_object(Cluster, pk)
    for key, value in data.items():
        setattr(obj, key, value)

    try:
        obj.save()
        return jsonify(obj.get_dict(expand=True))
    except:
        abort(500)


@api.route('/clusters/<pk>', methods=['DELETE'])
@jwt_required()
def cluster_delete(pk):
    obj = get_object(Cluster, pk)

    try:
        obj.delete()
    except:
        abort(500)

    return jsonify({'id': obj.id, 'state': 'deleted'})


@api.route('/clusters/<pk>/status', methods=['GET'])
@jwt_required()
def cluster_status(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.status())


@api.route('/clusters/<pk>/topology-data', methods=['GET'])
def cluster_topology_data(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.topology_data())


@api.route('/clusters/<pk>/kubeconfig', methods=['GET'])
@jwt_required()
def cluster_kubeconfig(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.kubeconfig)


# Provisioners

@api.route('/provisioners', methods=['GET'])
@jwt_required()
def provisioner_list():
    output = []

    for obj in list(Provisioner.list(return_objects=True).values()):
        output.append(obj.get_dict())

    return jsonify(output)


@api.route('/provisioners', methods=['POST'])
@jwt_required()
def provisioner_create():
    if not request.json:
        abort(400)
    else:
        obj = Provisioner(**request.json)
        try:
            obj.save()
            output = obj.get_dict(expand=True)
        except:
            abort(500)

    return jsonify(output)


@api.route('/provisioners/<pk>', methods=['GET'])
@jwt_required()
def provisioner_get(pk):
    obj = get_object(Provisioner, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/provisioners/<pk>', methods=['PATCH'])
@jwt_required()
def provisioner_update(pk):
    if not request.json:
        abort(400)

    data = request.json
    if not isinstance(data, dict):
        abort(400)

    obj = get_object(Provisioner, pk)
    for key, value in data.items():
        setattr(obj, key, value)

    try:
        obj.save()
        return jsonify(obj.get_dict(expand=True))
    except:
        abort(500)


@api.route('/provisioners/<pk>', methods=['DELETE'])
@jwt_required()
def provisioner_delete(pk):
    obj = get_object(Provisioner, pk)

    try:
        obj.delete()
    except:
        abort(500)

    return jsonify({'id': obj.id, 'state': 'deleted'})


# Organizations

@api.route('/organizations', methods=['GET'])
@jwt_required()
def organization_list():
    output = []

    for obj in list(Organization.list(return_objects=True).values()):
        output.append(obj.get_dict())

    return jsonify(output)


@api.route('/organizations', methods=['POST'])
@jwt_required()
def organization_create():
    if not request.json:
        abort(400)
    else:
        obj = Organization(**request.json)
        try:
            obj.save()
            output = obj.get_dict(expand=True)
        except:
            abort(500)

    return jsonify(output)


@api.route('/organizations/<pk>', methods=['GET'])
@jwt_required()
def organization_get(pk):
    obj = get_object(Organization, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/organizations/<pk>', methods=['PATCH'])
@jwt_required()
def organization_update(pk):
    if not request.json:
        abort(400)

    data = request.json
    if not isinstance(data, dict):
        abort(400)

    obj = get_object(Organization, pk)
    for key, value in data.items():
        setattr(obj, key, value)

    try:
        obj.save()
        return jsonify(obj.get_dict(expand=True))
    except:
        abort(500)


@api.route('/organizations/<pk>', methods=['DELETE'])
@jwt_required()
def organization_delete(pk):
    obj = get_object(Organization, pk)

    try:
        obj.delete()
    except:
        abort(500)

    return jsonify({'id': obj.id, 'state': 'deleted'})


# Users

@api.route('/users', methods=['GET'])
@jwt_required()
def user_list():
    output = []

    for obj in list(User.list(return_objects=True).values()):
        output.append(obj.get_dict())

    return jsonify(output)


@api.route('/users', methods=['POST'])
@jwt_required()
def user_create():
    if not request.json:
        abort(400)
    else:
        obj = User(**request.json)
        try:
            obj.save()
            output = obj.get_dict(expand=True)
        except:
            abort(500)

    return jsonify(output)


@api.route('/users/<pk>', methods=['GET'])
@jwt_required()
def user_get(pk):
    obj = get_object(User, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/users/<pk>', methods=['PATCH'])
@jwt_required()
def user_update(pk):
    if not request.json:
        abort(400)

    data = request.json
    if not isinstance(data, dict):
        abort(400)

    obj = get_object(User, pk)
    for key, value in data.items():
        setattr(obj, key, value)

    try:
        obj.save()
        return jsonify(obj.get_dict(expand=True))
    except:
        abort(500)


@api.route('/users/<pk>', methods=['DELETE'])
@jwt_required()
def user_delete(pk):
    obj = get_object(User, pk)

    try:
        obj.delete()
    except:
        abort(500)

    return jsonify({'id': obj.id, 'state': 'deleted'})
