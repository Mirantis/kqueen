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
        try:
            out = []
            kubernetes = KubernetesAPI(cluster=self)
            out.append(kubernetes.list_nodes())
            out.append(kubernetes.list_pods())
            out.append(kubernetes.list_services())
        except:
            out = []

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
