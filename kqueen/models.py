from importlib import import_module
from flask import current_app as app

from kqueen.kubeapi import KubernetesAPI
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import ModelMeta
from kqueen.storages.etcd import StringField

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#
# Model definition
#


class Cluster(Model, metaclass=ModelMeta):
    id = IdField()
    name = StringField()
    provisioner = StringField()
    state = StringField()
    kubeconfig = JSONField()
    metadata = JSONField()

    def get_state(self):
        if self.state != app.config['CLUSTER_PROVISIONING_STATE']:
            return self.state
        try:
            cluster = self.engine.cluster_get()
            if cluster['state'] == app.config['CLUSTER_PROVISIONING_STATE']:
                return self.state
            self.state = cluster['state']
            self.save()
        except:
            pass
        return self.state

    def get_provisioner(self):
        try:
            provisioner = Provisioner.load(self.provisioner)
        except:
            provisioner = None
        return provisioner

    @property
    def engine(self):
        provisioner = self.get_provisioner()
        if provisioner:
            _class = provisioner.get_engine_cls()
            if _class:
                parameters = provisioner.parameters or {}
                return _class(self, **parameters)
        return None

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
                'nodes': kubernetes.list_nodes(),
                'version': kubernetes.get_version(),
                'nodes_pods': kubernetes.count_pods_by_node(),
                'pods': kubernetes.list_pods(),
                'services': kubernetes.list_services(),
                'deployments': kubernetes.list_deployments(),
            }

        except:
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

        pods = kubernetes.list_pods()
        for pod in pods:
            pod['kind'] = 'Pod'

        services = kubernetes.list_services()
        for service in services:
            service['kind'] = 'Service'

        raw_data = nodes + pods + services

        resources = {datum['metadata']['uid']: datum for datum in raw_data}
        relations = []

        node_name_2_uid = {}
        service_run_2_uid = {}

        for resource_id, resource in resources.items():
            # Add node name to uid mapping
            if resource['kind'] == 'Node':
                node_name_2_uid[resource['metadata']['name']] = resource_id

            # Add service run selector to uid_mapping
            if resource['kind'] == 'Service' and resource['spec'].get('selector', {}) is not None:
                if resource['spec'].get('selector', {}).get('run', False):
                    service_run_2_uid[resource['spec']['selector']['run']] = resource_id

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
            if resource['kind'] == 'Pod':

                # define relationship between pods and nodes
                if resource['spec']['node_name'] is not None:
                    relations.append({
                        'source': resource_id,
                        'target': node_name_2_uid[resource['spec']['node_name']]
                    })

                # define relationships between pods and rep sets and
                # replication controllers
                if resource['metadata'].get('ownerReferences', False):
                    relations.append({
                        'source': resource['metadata']['ownerReferences'][0]['uid'],
                        'target': resource_id
                    })

                # rel'n between pods and services
                if resource['spec'].get('selector', {}).get('run', False):
                    relations.append({
                        'source': resource_id,
                        'target': service_run_2_uid(resource['metadata']['labels']['run'])
                    })

        out = {
            'items': resources,
            'relations': relations,
            'kinds': {
                'Pod': '',
            }
        }
#        except:
#            out = {
#                'items': [],
#                'relations': []
#            }

        return out


class Provisioner(Model, metaclass=ModelMeta):
    id = IdField()
    name = StringField()
    engine = StringField()
    state = StringField()
    parameters = JSONField()

    def get_engine_cls(self):
        """Return engine class"""
        try:
            module_path = '.'.join(self.engine.split('.')[:-1])
            class_name = self.engine.split('.')[-1]
            module = import_module(module_path)
            _class = getattr(module, class_name)
        except:
            _class = None
        return _class

    @property
    def engine_name(self):
        return getattr(self.get_engine_cls(), 'verbose_name', self.engine)

    def engine_status(self, save=True):
        state = app.config['PROVISIONER_UNKNOWN_STATE']
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
        return super(Provisioner, self).save()
