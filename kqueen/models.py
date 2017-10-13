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
        klass = self.get_engine_cls()
        if klass:
            state = klass.engine_status()
        if save:
            self.state = state
            self.save()
        return state

    def save(self, check_status=True):
        if check_status:
            self.state = self.engine_status(save=False)
        return super(Provisioner, self).save()
