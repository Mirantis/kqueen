from .helpers import get_object
from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask import request
from flask_jwt import current_identity
from flask_jwt import jwt_required
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from .generic_views import ListView, CreateView, GetView, UpdateView, UpdateView, DeleteView

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
class ListClusters(ListView):
    object_class = Cluster

class CreateCluster(CreateView):
    object_class = Cluster

    def after_save(self):
        # start provisioning
        prov_status, prov_msg = self.obj.engine.provision()

        if not prov_status:
            logger.error('Provisioning failed: {}'.format(prov_msg))
            abort(500)

class GetCluster(GetView):
    object_class = Cluster

class UpdateCluster(UpdateView):
    object_class = Cluster

class DeleteCluster(DeleteView):
    object_class = Cluster

api.add_url_rule('/clusters', view_func=ListClusters.as_view('cluster_list'))
api.add_url_rule('/clusters', view_func=CreateCluster.as_view('cluster_create'))
api.add_url_rule('/clusters/<uuid:pk>', view_func=GetCluster.as_view('cluster_get'))
api.add_url_rule('/clusters/<uuid:pk>', view_func=UpdateCluster.as_view('cluster_update'))
api.add_url_rule('/clusters/<uuid:pk>', view_func=DeleteCluster.as_view('cluster_delete'))


@api.route('/clusters/<uuid:pk>/status', methods=['GET'])
@jwt_required()
def cluster_status(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.status())


@api.route('/clusters/<uuid:pk>/topology-data', methods=['GET'])
def cluster_topology_data(pk):
    obj = get_object(Cluster, pk)

    return jsonify(obj.topology_data())


@api.route('/clusters/<uuid:pk>/kubeconfig', methods=['GET'])
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
        output.append(obj.get_dict(expand=True))

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


@api.route('/provisioners/<uuid:pk>', methods=['GET'])
@jwt_required()
def provisioner_get(pk):
    obj = get_object(Provisioner, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/provisioners/<uuid:pk>', methods=['PATCH'])
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


@api.route('/provisioners/<uuid:pk>', methods=['DELETE'])
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
        output.append(obj.get_dict(expand=True))

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


@api.route('/organizations/<uuid:pk>', methods=['GET'])
@jwt_required()
def organization_get(pk):
    obj = get_object(Organization, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/organizations/<uuid:pk>', methods=['PATCH'])
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


@api.route('/organizations/<uuid:pk>', methods=['DELETE'])
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
        output.append(obj.get_dict(expand=True))

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


@api.route('/users/<uuid:pk>', methods=['GET'])
@jwt_required()
def user_get(pk):
    obj = get_object(User, pk)

    return jsonify(obj.get_dict(expand=True))


@api.route('/users/<uuid:pk>', methods=['PATCH'])
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


@api.route('/users/<uuid:pk>', methods=['DELETE'])
@jwt_required()
def user_delete(pk):
    obj = get_object(User, pk)

    try:
        obj.delete()
    except:
        abort(500)

    return jsonify({'id': obj.id, 'state': 'deleted'})


@api.route('/users/whoami', methods=['GET'])
@jwt_required()
def user_whoami():
    output = current_identity

    return jsonify(output)
