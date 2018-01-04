from .manual import ManualEngine
from flask import url_for
from kqueen.conftest import auth_header
from kqueen.conftest import user
from kqueen.models import Cluster
from kqueen.models import Provisioner

import json
import pytest
import yaml

KUBECONFIG = yaml.load(open('kubeconfig_localhost', 'r').read())
CLUSTER_METADATA = {
    'minion_count': 10,
    'cluster_type': 'ha',
    'kubeconfig': KUBECONFIG
}

PROVISIONER_PARAMETERS = {
    'credentials': 'username:password',
}


@pytest.mark.usefixtures('client_class')
class ManualEngineBase:
    def setup(self):
        _user = user()
        create_kwargs_provisioner = {
            'name': 'Testing manual',
            'engine': 'kqueen.engines.ManualEngine',
            'parameters': PROVISIONER_PARAMETERS,
            'owner': _user
        }

        prov = Provisioner(_user.namespace, **create_kwargs_provisioner)
        prov.save(check_status=False)

        self.create_kwargs_cluster = {
            'name': 'Testing cluster for manual provisioner',
            'provisioner': prov,
            'state': 'deployed',
            'kubeconfig': KUBECONFIG,
            'metadata': CLUSTER_METADATA,
            'owner': _user
        }

        self.cluster = Cluster.create(_user.namespace, **self.create_kwargs_cluster)
        self.engine = ManualEngine(cluster=self.cluster)

        # client setup
        self.auth_header = auth_header(self.client)
        self.namespace = self.auth_header['X-Test-Namespace']


class TestClusterAction(ManualEngineBase):
    def test_initialization(self):
        assert self.engine.cluster.get_dict(True) == self.cluster.get_dict(True)

    def test_cluster_list(self):
        assert self.engine.cluster_list() == []

    def test_cluster_get(self):
        assert self.engine.cluster_get() == {}

    @pytest.mark.parametrize('action', ['provision', 'deprovision'])
    def test_actions(self, action):
        method = getattr(self.engine, action)

        assert method() == (True, None)

    def test_get_kubeconfig(self):
        assert self.cluster.engine.get_kubeconfig() == self.cluster.kubeconfig

    def test_progress(self):
        progress = self.engine.get_progress()

        assert 'response' in progress
        assert 'progress' in progress
        assert 'result' in progress

    def test_engine_status(self):
        assert self.engine.engine_status()

    def test_parameter_schema(self):
        assert self.engine.get_parameter_schema() == self.engine.parameter_schema


class TestCreateOverAPI(ManualEngineBase):
    def test_create_over_api(self):
        """Verify Cluster is created over API and kubeconfig is set"""

        url = url_for('api.cluster_list')
        data = self.create_kwargs_cluster
        data['provisioner'] = 'Provisioner:{}'.format(data['provisioner'].id)
        data['owner'] = 'User:{}'.format(data['owner'].id)

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
        validation, _ = obj.validate()
        assert validation

        # check parameters
        assert obj.kubeconfig == data['kubeconfig']

        return obj

    @pytest.mark.parametrize('metadata_name', list(CLUSTER_METADATA.keys()))
    def test_metadata_parameters_direct(self, metadata_name):
        assert metadata_name in self.cluster.metadata
        assert self.cluster.metadata[metadata_name] == CLUSTER_METADATA[metadata_name]

    @pytest.mark.parametrize('metadata_name', list(CLUSTER_METADATA.keys()))
    def test_metadata_parameters_api(self, metadata_name):
        obj = self.test_create_over_api()

        assert metadata_name in obj.metadata
        assert obj.metadata[metadata_name] == CLUSTER_METADATA[metadata_name]

    @pytest.mark.parametrize('param_name', list(CLUSTER_METADATA.keys()) + list(PROVISIONER_PARAMETERS.keys()))
    def test_engine_gets_parameters(self, param_name, monkeypatch):
        obj = self.test_create_over_api()

        def fake_init(self, cluster, **kwargs):
            self.cluster = cluster
            self.test_kwargs = kwargs

        monkeypatch.setattr(ManualEngine, '__init__', fake_init)

        engine = obj.engine

        assert param_name in engine.test_kwargs

    def test_delete_run_deprovision(self, monkeypatch):
        """"Deprovision is called before cluster delete"""

        def fake_deprovision(self):
            self.cluster.metadata['_deprovisioned'] = True
            self.cluster.save()

            return True, None

        monkeypatch.setattr(ManualEngine, 'deprovision', fake_deprovision)

        obj = self.test_create_over_api()
        obj.delete()

        assert '_deprovisioned' in obj.metadata
        assert obj.metadata['_deprovisioned']

    def test_delete_remove_object(self):
        obj = self.test_create_over_api()
        obj.delete()

        assert not Cluster.exists(self.namespace, obj.id)
