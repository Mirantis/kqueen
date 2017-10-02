from importlib import import_module

from kqueen.kubeapi import KubernetesAPI
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import StringField
from kqueen.storages.etcd import SecretField

#
# Model definition
#


class Cluster(Model):
    id = IdField()
    name = StringField()
    provisioner = StringField()
    state = StringField()
    kubeconfig = JSONField()

    def status(self):
        """Return information about Kubernetes cluster"""

        kubernetes = KubernetesAPI(cluster=self)

        out = {
            'nodes': kubernetes.list_nodes(),
            'version': kubernetes.get_version(),
        }

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

