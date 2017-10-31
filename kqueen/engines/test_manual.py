from .manual import ManualEngine
from kqueen.models import Cluster
from kqueen.models import Provisioner

import yaml
import pytest


class TestManualEngine:
    def setup(self):
        create_kwargs_provisioner = {
            'name': 'Testing manual',
            'engine': 'kqueen.engines.ManualEngine'
        }

        prov = Provisioner(**create_kwargs_provisioner)
        prov.save(check_status=False)

        create_kwargs_cluster = {
            'name': 'Testing cluster for manual provisioner',
            'provisioner': prov,
            'state': 'deployed',
            'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
        }

        self.cluster = Cluster.create(**create_kwargs_cluster)
        self.engine = ManualEngine(cluster=self.cluster)

    def test_initialization(self):
        assert self.engine.cluster == self.cluster

    def test_cluster_list(self):
        assert self.engine.cluster_list() == []

    def test_cluster_get(self):
        assert self.engine.cluster_get() == self.cluster

    @pytest.mark.parametrize('action', ['provision', 'deprovision'])
    def test_actions(self, action):
        method = getattr(self.engine, action)

        assert method() == (True, None)

    def test_get_kubeconfig(self):
        assert self.engine.get_kubeconfig() == self.cluster.kubeconfig

    def test_progress(self):
        progress = self.engine.get_progress()

        assert 'response' in progress
        assert 'progress' in progress
        assert 'result' in progress

    def test_engine_status(self):
        assert self.engine.engine_status()

    def test_parameter_schema(self):
        assert self.engine.get_parameter_schema() == {}
