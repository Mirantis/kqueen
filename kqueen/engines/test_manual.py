from .manual import ManualEngine
from flask import url_for
from kqueen.conftest import auth_header
from kqueen.conftest import user
from kqueen.models import Cluster
from kqueen.models import Provisioner

import json
import pytest
import yaml


@pytest.mark.usefixtures('client_class')
class TestManualEngine:
    def setup(self):
        _user = user()
        create_kwargs_provisioner = {
            'name': 'Testing manual',
            'engine': 'kqueen.engines.ManualEngine'
        }

        prov = Provisioner(_user.namespace, **create_kwargs_provisioner)
        prov.save(check_status=False)

        self.create_kwargs_cluster = {
            'name': 'Testing cluster for manual provisioner',
            'provisioner': prov,
            'state': 'deployed',
            'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
        }

        self.cluster = Cluster.create(_user.namespace, **self.create_kwargs_cluster)
        self.engine = ManualEngine(cluster=self.cluster)

        # client setup
        self.auth_header = auth_header(self.client)
        self.namespace = self.auth_header['X-Test-Namespace']

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

    def test_create_over_api(self):
        """Verify Cluster is created over API and kubeconfig is set"""

        url = url_for('api.cluster_list')
        data = self.create_kwargs_cluster
        data['provisioner'] = 'Provisioner:{}'.format(data['provisioner'].id)

        # create
        response = self.client.post(
            url,
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json'
        )

        assert response.status_code == 200

        # load
        cluster_id = response.json['id']
        obj = Cluster.load(self.namespace, cluster_id)
        assert obj.validate()

        # check parameters
        assert obj.kubeconfig == data['kubeconfig']
