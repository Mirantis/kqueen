from importlib import import_module
from kqueen.kubeapi import KubernetesAPI
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import ModelMeta
from kqueen.storages.etcd import SecretField
from kqueen.storages.etcd import StringField

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#
# Model definition
#


class Cluster(Model, metaclass=ModelMeta):
    id = IdField()
    external_id = StringField()
    name = StringField()
    provisioner = StringField()
    state = StringField()
    kubeconfig = JSONField()

    def get_state(self):
        if self.state != 'Deploying':
            return self.state
        try:
            prv = self.get_provisioner().engine_cls()
            c_data = prv.get(str(self.id))
            if c_data['state'] == 'Deploying':
                return self.state
            self.state = 'OK' if c_data['state'] == 'SUCCESS' else 'Error'
            self.save()
            return self.state
        except:
            pass
        return self.state

    def get_provisioner(self):
        try:
            prv = Provisioner.load(self.provisioner)
        except:
            prv = None
        return prv

    def get_external_id(self):
        if self.external_id:
            return self.external_id
        try:
            prv = self.get_provisioner().engine_cls()
            c_data = prv.get(str(self.id))
            external_id = c_data['build_number']
            self.external_id = external_id
            self.save()
            return external_id
        except:
            pass
        return None

    def get_kubeconfig(self):
        if self.kubeconfig:
            return self.kubeconfig
        if self.get_external_id():
            try:
                kubeconfig = self.get_provisioner().engine_cls().get_kubeconfig(self.external_id)
                self.kubeconfig = kubeconfig
                self.save()
                return kubeconfig
            except:
                pass
        return {}

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

#                logger.info(resource['spec'])
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
    # TODO: Do not hardcode AWS specific params, just create JSONField with
    # params then pass params field as argument to class saved in type field
    access_id = StringField()
    access_key = SecretField()
    location = StringField()

    @property
    def engine_cls(self):
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
        return self.engine_cls.__name__ if self.engine_cls else self.engine

    def alive(self):
        """Test availability of provisioner and return bool"""
        return True

