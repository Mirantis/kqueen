from .helpers import get_object
from flask import abort
from flask import Blueprint
from flask import jsonify
from flask import make_response
from flask_jwt import current_identity
from flask_jwt import jwt_required
from importlib import import_module
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from .generic_views import ListView, CreateView, GetView, UpdateView, DeleteView

import logging
import os
import yaml

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
            abort(500, description=prov_msg)


class GetCluster(GetView):
    object_class = Cluster

    def dispatch_request(self, *args, **kwargs):
        self.check_access()

        cluster = self.get_content(*args, **kwargs)
        cluster.get_state()

        return jsonify(cluster)


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
    obj = get_object(Cluster, pk, current_identity)

    return jsonify(obj.status())


@api.route('/clusters/<uuid:pk>/topology-data', methods=['GET'])
@jwt_required()
def cluster_topology_data(pk):
    obj = get_object(Cluster, pk, current_identity)

    return jsonify(obj.topology_data())


@api.route('/clusters/<uuid:pk>/kubeconfig', methods=['GET'])
@jwt_required()
def cluster_kubeconfig(pk):
    obj = get_object(Cluster, pk, current_identity)

    return jsonify(obj.kubeconfig)


# Provisioners
class ListProvisioners(ListView):
    object_class = Provisioner


class CreateProvisioner(CreateView):
    object_class = Provisioner


class GetProvisioner(GetView):
    object_class = Provisioner


class UpdateProvisioner(UpdateView):
    object_class = Provisioner


class DeleteProvisioner(DeleteView):
    object_class = Provisioner


api.add_url_rule('/provisioners', view_func=ListProvisioners.as_view('provisioner_list'))
api.add_url_rule('/provisioners', view_func=CreateProvisioner.as_view('provisioner_create'))
api.add_url_rule('/provisioners/<uuid:pk>', view_func=GetProvisioner.as_view('provisioner_get'))
api.add_url_rule('/provisioners/<uuid:pk>', view_func=UpdateProvisioner.as_view('provisioner_update'))
api.add_url_rule('/provisioners/<uuid:pk>', view_func=DeleteProvisioner.as_view('provisioner_delete'))


@api.route('/provisioners/engines', methods=['GET'])
@jwt_required()
def provisioner_engine_list():
    from kqueen.engines import __all__ as ENGINES
    engine_cls = []
    module_path = 'kqueen.engines'
    for engine in ENGINES:
        try:
            module = import_module(module_path)
            _class = getattr(module, engine)
            parameters = _class.get_parameter_schema()
            engine_cls.append({
                'name': '.'.join([module_path, engine]),
                'parameters': parameters
            })
        except NotImplementedError:
            engine_cls.append({
                'name': engine,
                'parameters': {
                    'provisioner': {},
                    'cluster': {}
                }
            })
        except Exception:
            logger.error('Unable to read parameters for engine {}'.format(engine))

    return jsonify(engine_cls)


# Organizations
class ListOrganizations(ListView):
    object_class = Organization


class CreateOrganization(CreateView):
    object_class = Organization


class GetOrganization(GetView):
    object_class = Organization


class UpdateOrganization(UpdateView):
    object_class = Organization


class DeleteOrganization(DeleteView):
    object_class = Organization


api.add_url_rule('/organizations', view_func=ListOrganizations.as_view('organization_list'))
api.add_url_rule('/organizations', view_func=CreateOrganization.as_view('organization_create'))
api.add_url_rule('/organizations/<uuid:pk>', view_func=GetOrganization.as_view('organization_get'))
api.add_url_rule('/organizations/<uuid:pk>', view_func=UpdateOrganization.as_view('organization_update'))
api.add_url_rule('/organizations/<uuid:pk>', view_func=DeleteOrganization.as_view('organization_delete'))


# Users
class ListUsers(ListView):
    object_class = User


class CreateUser(CreateView):
    object_class = User


class GetUser(GetView):
    object_class = User


class UpdateUser(UpdateView):
    object_class = User


class DeleteUser(DeleteView):
    object_class = User


api.add_url_rule('/users', view_func=ListUsers.as_view('user_list'))
api.add_url_rule('/users', view_func=CreateUser.as_view('user_create'))
api.add_url_rule('/users/<uuid:pk>', view_func=GetUser.as_view('user_get'))
api.add_url_rule('/users/<uuid:pk>', view_func=UpdateUser.as_view('user_update'))
api.add_url_rule('/users/<uuid:pk>', view_func=DeleteUser.as_view('user_delete'))


@api.route('/users/whoami', methods=['GET'])
@jwt_required()
def user_whoami():
    output = current_identity

    return jsonify(output)


@api.route('/swagger', methods=['GET'])
def swagger_json():
    try:
        base_path = os.path.abspath(os.path.dirname(__file__))
        file_path = os.path.join(base_path, 'api.yml')
        with open(file_path, 'r') as f:
            _yaml = f.read()
        data = yaml.safe_load(_yaml)
    except FileNotFoundError:
        logger.error('Swagger YAML not found on {}.'.format(file_path))
        abort(404)
    except Exception as e:
        logger.error(e)
        abort(500)

    return jsonify(data)
