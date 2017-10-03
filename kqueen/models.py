from importlib import import_module

from kqueen.kubeapi import KubernetesAPI
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import StringField
from kqueen.storages.etcd import SecretField

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

#
# Model definition
#

class Cluster(Model):
    id = IdField()
    external_id = StringField()
    name = StringField()
    provisioner = StringField()
    state = StringField()
    kubeconfig = JSONField()

    def get_state(self):
        if self.state.value != 'Deploying':
            return self.state.value
        try:
            prv = self.get_provisioner().engine_cls()
            c_data = prv.get(str(self.id))
            if c_data['state'] == 'Deploying':
                return self.state.value
            self.state.value = 'OK' if c_data['state'] == 'SUCCESS' else 'FAIL'
            self.save()
            return self.state.value
        except:
            pass
        return self.state.value

    def get_provisioner(self):
        try:
            prv = Provisioner.load(self.provisioner)
        except:
            prv = None
        return prv

    def get_external_id(self):
        if self.external_id.value:
            return self.external_id.value
        try:
            prv = self.get_provisioner().engine_cls()
            c_data = prv.get(str(self.id))
            external_id = c_data['build_number']
            self.external_id.value = external_id
            self.save()
            return external_id
        except:
            pass
        return None

    def get_kubeconfig(self):
        if self.kubeconfig.value:
            return self.kubeconfig.value
        if self.get_external_id():
            try:
                kubeconfig = self.get_provisioner().engine_cls().get_kubeconfig(self.external_id)
                self.kubeconfig.value = kubeconfig
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


class Provisioner(Model):
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
            module_path = '.'.join(self.engine.value.split('.')[:-1])
            class_name = self.engine.value.split('.')[-1]
            module = import_module(module_path)
            _class = getattr(module, class_name)
        except:
            _class = None
        return _class

    @property
    def engine_name(self):
        return self.engine_cls.__name__ if self.engine_cls else self.engine.value

    def alive(self):
        """Test availability of provisioner and return bool"""
        return True

