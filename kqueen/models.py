from datetime import datetime
from datetime import timedelta
from importlib import import_module
from kqueen.config import current_config
from kqueen.kubeapi import KubernetesAPI
from kqueen.storages.etcd import BoolField
from kqueen.storages.etcd import DatetimeField
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import ModelMeta
from kqueen.storages.etcd import PasswordField
from kqueen.storages.etcd import RelationField
from kqueen.storages.etcd import StringField
from tempfile import mkstemp

import logging
import os
import subprocess
import yaml

logger = logging.getLogger('kqueen_api')
config = current_config()

#
# Model definition
#


class Cluster(Model, metaclass=ModelMeta):
    id = IdField(required=True)
    name = StringField(required=True)
    provisioner = RelationField(remote_class_name='Provisioner')
    state = StringField()
    kubeconfig = JSONField(encrypted=True)
    metadata = JSONField()
    created_at = DatetimeField(default=datetime.utcnow)
    owner = RelationField(required=True, remote_class_name='User')

    def get_state(self):
        try:
            remote_cluster = self.engine.cluster_get()
        except Exception as e:
            logger.exception('Unable to get data from backend for cluster {}'.format(self.name))
            remote_cluster = {}

        if 'state' in remote_cluster:

            self.set_status(remote_cluster)
            if remote_cluster['state'] == self.state:
                return self.state

            self.state = remote_cluster['state']
            self.save()
        else:
            self.state = config.get('CLUSTER_UNKNOWN_STATE')
            self.save()

        # check for stale clusters
        max_age = timedelta(seconds=config.get('PROVISIONER_TIMEOUT'))
        if self.state == config.get('CLUSTER_PROVISIONING_STATE') and datetime.utcnow() - self.created_at > max_age:
            self.state = config.get('CLUSTER_ERROR_STATE')
            self.save()

        return self.state

    def set_status(self, cluster):
        detailed_status = cluster.get('metadata', {}).get('status_message')
        if detailed_status:
            self.metadata['status_message'] = detailed_status
            self.save()

    @property
    def engine(self):
        if self.provisioner:
            _class = self.provisioner.get_engine_cls()
            if _class:
                parameters = {}
                for i in [self.provisioner.parameters, self.metadata]:
                    if isinstance(i, dict):
                        parameters.update(i)

                return _class(self, **parameters)
        else:
            raise Exception('Missing provisioner')

    def delete(self):
        """Deprovision cluster and delete object from database"""

        deprov_status, deprov_msg = self.engine.deprovision()

        if deprov_status:
            super().delete()
        else:
            raise Exception('Unable to deprovision cluster: {}'.format(deprov_msg))

    def get_kubeconfig(self):
        if self.kubeconfig:
            return self.kubeconfig
        kubeconfig = self.engine.get_kubeconfig()
        self.kubeconfig = kubeconfig
        self.save()
        return kubeconfig

    def save(self, **kwargs):
        # while used in async method, app context is not available by default and needs to be imported
        from flask import current_app as app
        from kqueen.server import create_app
        try:
            if not app.testing:
                app = create_app()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            return super().save(**kwargs)

    def status(self):
        """Return information about Kubernetes cluster"""
        try:
            kubernetes = KubernetesAPI(cluster=self)

            out = {
                'addons': kubernetes.list_services(filter_addons=True),
                'deployments': kubernetes.list_deployments(),
                'namespaces': kubernetes.list_namespaces(),
                'nodes': kubernetes.list_nodes(),
                'nodes_pods': kubernetes.count_pods_by_node(),
                'persistent_volumes': kubernetes.list_persistent_volumes(),
                'persistent_volume_claims': kubernetes.list_persistent_volume_claims(),
                'pods': kubernetes.list_pods(),
                'replica_sets': kubernetes.list_replica_sets(),
                'services': kubernetes.list_services(),
                'version': kubernetes.get_version(),
            }
        except Exception as e:
            logger.exception(e)
            out = {}

        return out

    def topology_data(self):
        """
        Return information about Kubernetes cluster in format used in
        visual processing.
        """
        raw_data = []
        kubernetes = KubernetesAPI(cluster=self)

        nodes = kubernetes.list_nodes()
        for node in nodes:
            node['kind'] = 'Node'

        pods = kubernetes.list_pods(False)
        for pod in pods:
            pod['kind'] = 'Pod'

        namespaces = kubernetes.list_namespaces()
        for namespace in namespaces:
            namespace['kind'] = 'Namespace'

        services = kubernetes.list_services(False)
        for service in services:
            service['kind'] = 'Service'

        deployments = kubernetes.list_deployments(False)
        for deployment in deployments:
            deployment['kind'] = 'Deployment'

        replica_sets = kubernetes.list_replica_sets(False)
        replica_set_dict = {datum['metadata']['uid']: datum for datum in replica_sets}

        raw_data = nodes + pods + services + deployments + namespaces

        resources = {datum['metadata']['uid']: datum for datum in raw_data}
        relations = []

        namespace_name_2_uid = {}
        node_name_2_uid = {}
        service_select_run_2_uid = {}
        service_select_app_2_uid = {}

        for resource_id, resource in resources.items():
            # Add node name to uid mapping
            if resource['kind'] == 'Node':
                node_name_2_uid[resource['metadata']['name']] = resource_id

            # Add node name to uid mapping
            if resource['kind'] == 'Namespace':
                namespace_name_2_uid[resource['metadata']['name']] = resource_id

            # Add service run selector to uid_mapping
            if resource['kind'] == 'Service' and resource['spec'].get('selector', {}) is not None:
                if resource['spec'].get('selector', {}).get('run', False):
                    service_select_run_2_uid[resource['spec']['selector']['run']] = resource_id
                if resource['spec'].get('selector', {}).get('app', False):
                    service_select_app_2_uid[resource['spec']['selector']['app']] = resource_id

            # Add Containers as top-level resource
            """
            if resource['kind'] == 'Pod':
                for container in resource['spec']['containers']:
                    container_id = "{1}-{2}".format(
                        resource['metadata']['uid'], container['name'])
                    resources[container_id] = {
                        'metadata': container,
                        'kind': 'Container'
                    }
                    relations.append({
                        'source': resource_id,
                        'target': container_id,
                    })
            """

        for resource_id, resource in resources.items():
            if resource['kind'] not in ('Node', 'Namespace'):
                relations.append({
                    'source': resource_id,
                    'target': namespace_name_2_uid[resource['metadata']['namespace']]
                })

            if resource['kind'] == 'Pod':

                # define relationship between pods and nodes
                if resource['spec']['node_name'] is not None:
                    relations.append({
                        'source': resource_id,
                        'target': node_name_2_uid[resource['spec']['node_name']]
                    })

                # define relationships between pods and rep sets and
                # replication controllers
                if resource['metadata'].get('owner_references', False):
                    if resource['metadata']['owner_references'][0]['kind'] == 'ReplicaSet':
                        rep_set_id = resource['metadata']['owner_references'][0]['uid']
                        deploy_id = replica_set_dict[rep_set_id]['metadata']['owner_references'][0]['uid']
                        relations.append({
                            'source': deploy_id,
                            'target': resource_id
                        })

                # rel'n between pods and services
                if resource.get('metadata', {}).get('labels', {}).get('run', False):
                    relations.append({
                        'source': resource_id,
                        'target': service_select_run_2_uid[resource['metadata']['labels']['run']]
                    })

                if resource.get('metadata', {}).get('labels', {}).get('app', False):
                    try:
                        relations.append({
                            'source': resource_id,
                            'target': service_select_app_2_uid[resource['metadata']['labels']['app']]
                        })
                    except Exception:
                        pass

        out = {
            'items': resources,
            'relations': relations,
            'kinds': {
                'Pod': '',
            }
        }
#        except Exception:
#            out = {
#                'items': [],
#                'relations': []
#            }

        return out

    def get_kubeconfig_file(self):
        """
        Create file with kubeconfig and make this file available on filesystem.

        Returns:
            str: Filename (including path).

        """

        if hasattr(self, 'kubeconfig_path') and os.path.isfile(self.kubeconfig_path):
            return self.kubeconfig_path

        # create kubeconfig file
        filehandle, file_path = mkstemp()
        filehandle = open(filehandle, 'w')
        filehandle.write(yaml.dump(self.kubeconfig))
        self.kubeconfig_path = file_path

        return file_path

    def apply(self, resource_text):
        """
        Apply YAML file supplied as text

        Args:
            resource_text (text): Content of file to apply

        Returns:
            tuple: (return_code, stdout)


        """
        kubeconfig = self.get_kubeconfig_file()

        # create temporary resource file
        # TODO: create helper for this
        filehandle, file_path = mkstemp()
        filehandle = open(filehandle, 'w')
        filehandle.write(resource_text)
        filehandle.close()

        # apply resource file
        cmd = ['kubectl', '--kubeconfig', kubeconfig, 'apply', '-f', file_path]

        # TODO: validate output
        run = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        return run


class Provisioner(Model, metaclass=ModelMeta):
    id = IdField(required=True)
    name = StringField(required=True)
    verbose_name = StringField(required=False)
    engine = StringField(required=True)
    state = StringField(default=config.get('PROVISIONER_UNKNOWN_STATE'))
    parameters = JSONField(encrypted=True, default={})
    created_at = DatetimeField(default=datetime.utcnow)
    owner = RelationField(required=True, remote_class_name='User')

    @classmethod
    def list_engines(self):
        """Read engines and filter them according to whitelist"""

        engines = config.get('PROVISIONER_ENGINE_WHITELIST')

        if engines is None:
            from kqueen.engines import __all__ as engines_available
            engines = engines_available

        return engines

    def get_engine_cls(self):
        """Return engine class"""
        try:
            module_path = '.'.join(self.engine.split('.')[:-1])
            class_name = self.engine.split('.')[-1]
            module = import_module(module_path)
            _class = getattr(module, class_name)
        except Exception as e:
            logger.exception('Error')
            _class = None

        return _class

    def engine_status(self, save=True):
        state = config.get('PROVISIONER_UNKNOWN_STATE')
        engine_class = self.get_engine_cls()

        if engine_class:
            state = engine_class.engine_status(**self.parameters)
        if save:
            self.state = state
            self.save(check_status=False)
        return state

    def save(self, check_status=True, **kwargs):
        # while used in async method, app context is not available by default and needs to be imported
        from flask import current_app as app
        from kqueen.server import create_app
        try:
            if not app.testing:
                app = create_app()
        except RuntimeError:
            app = create_app()

        with app.app_context():
            if check_status:
                self.state = self.engine_status(save=False)
            self.verbose_name = getattr(self.get_engine_cls(), 'verbose_name', self.engine)
            return super().save(**kwargs)


#
# AUTHENTICATION
#


class Organization(Model, metaclass=ModelMeta):
    global_namespace = True

    id = IdField(required=True)
    name = StringField(required=True)
    namespace = StringField(required=True, unique=True)
    policy = JSONField()
    created_at = DatetimeField(default=datetime.utcnow)

    def is_deletable(self):
        remaining = []
        if User.list(self.namespace, return_objects=False):
            all_users = User.list(None).values()
            users = [u for u in all_users if u.namespace == self.namespace]
            for user in users:
                remaining.append({
                    'object': 'User',
                    'name': user.username,
                    'uuid': user.id
                })
        if Provisioner.list(self.namespace, return_objects=False):
            provisioners = Provisioner.list(self.namespace).values()
            for provisioner in provisioners:
                remaining.append({
                    'object': 'Provisioner',
                    'name': provisioner.name,
                    'uuid': provisioner.id
                })
        if Cluster.list(self.namespace, return_objects=False):
            clusters = Cluster.list(self.namespace).values()
            for cluster in clusters:
                remaining.append({
                    'object': 'Cluster',
                    'name': cluster.name,
                    'uuid': cluster.id
                })
        if remaining:
            return False, remaining
        return True, remaining

    def delete(self):
        deletable, remaining = self.is_deletable()
        if deletable:
            return super().delete()
        resource_list = []
        for resource in remaining:
            resource_string = '{} {}'.format(resource['object'].lower(), resource['uuid'])
            resource_list.append(resource_string)
        resources = ', '.join(resource_list)
        raise Exception('Cannot delete Organization {}, following resources needs to be deleted first: {}'.format(self.id, resources))


class User(Model, metaclass=ModelMeta):
    global_namespace = True

    id = IdField(required=True)
    username = StringField(required=True, unique=True)
    email = StringField(required=False, unique=True)
    password = PasswordField(required=True)
    organization = RelationField(required=True, remote_class_name='Organization')
    created_at = DatetimeField(default=datetime.utcnow)
    role = StringField(required=True)
    active = BoolField(required=True)
    metadata = JSONField(required=False)
    auth = StringField()

    @property
    def namespace(self):
        """
        Get namespace from organization.

        Returns:
            str: Namespace (from organization)
        """

        return self.organization.namespace
