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

logger = logging.getLogger(__name__)
config = current_config()

#
# Model definition
#


class Cluster(Model, metaclass=ModelMeta):
    id = IdField(required=True)
    name = StringField(required=True)
    provisioner = RelationField()
    state = StringField()
    kubeconfig = JSONField(encrypted=True)
    metadata = JSONField()
    created_at = DatetimeField()
    owner = RelationField(required=True)

    def get_state(self):
        try:
            cluster = self.engine.cluster_get()
        except Exception as e:
            logger.error('Unable to get data from backend for cluster {}'.format(self.name))
            cluster = {}

        if 'state' in cluster:
            if cluster['state'] == self.state:
                return self.state
            self.state = cluster['state']
            self.save()

        return self.state

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
            super(Cluster, self).delete()
        else:
            raise Exception('Unable to deprovision cluster: {}'.format(deprov_msg))

    def get_kubeconfig(self):
        if self.kubeconfig:
            return self.kubeconfig
        kubeconfig = self.engine.get_kubeconfig()
        self.kubeconfig = kubeconfig
        self.save()
        return kubeconfig

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

        except Exception:
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
    state = StringField()
    parameters = JSONField(encrypted=True)
    created_at = DatetimeField()
    owner = RelationField(required=True)

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
            logger.error(repr(e))
            _class = None

        return _class

    def engine_status(self, save=True):
        state = config.get('PROVISIONER_UNKNOWN_STATE')
        engine_class = self.get_engine_cls()
        if engine_class:
            state = engine_class.engine_status()
        if save:
            self.state = state
            self.save()
        return state

    def alive(self):
        """Test availability of provisioner and return bool"""
        return True

    def save(self, check_status=True):
        if check_status:
            self.state = self.engine_status(save=False)
        self.verbose_name = getattr(self.get_engine_cls(), 'verbose_name', self.engine)
        return super(Provisioner, self).save()


#
# AUTHENTICATION
#


class Organization(Model, metaclass=ModelMeta):
    global_namespace = True

    id = IdField(required=True)
    name = StringField(required=True)
    namespace = StringField(required=True)
    policy = JSONField()
    created_at = DatetimeField()


class User(Model, metaclass=ModelMeta):
    global_namespace = True

    id = IdField(required=True)
    username = StringField(required=True)
    email = StringField(required=False)
    password = PasswordField(required=True)
    organization = RelationField(required=True)
    created_at = DatetimeField()
    role = StringField(required=True)
    active = BoolField(required=True)
    metadata = JSONField(required=False)

    @property
    def namespace(self):
        """
        Get namespace from organization.

        Returns:
            str: Namespace (from organization)
        """

        return self.organization.namespace
