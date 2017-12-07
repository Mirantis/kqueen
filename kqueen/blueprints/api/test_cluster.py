from flask import url_for
from uuid import uuid4
from kqueen.conftest import cluster
from .test_crud import BaseTestCRUD

import pytest
import json


class TestClusterCRUD(BaseTestCRUD):
    def get_object(self):
        obj = cluster()

        return obj

    def get_edit_data(self):
        return {'name': 'patched cluster'}

    def get_create_data(self):
        data = self.obj.get_dict()
        data['id'] = None
        data['provisioner'] = 'Provisioner:{}'.format(self.obj.provisioner.id)

        return data

    def test_get_dict_expanded(self):

        dicted = self.obj.get_dict(expand=True)
        assert dicted['provisioner']['id'] == self.obj.provisioner.id

    def test_cluster_get(self):

        cluster_id = self.obj.id

        response = self.client.get(
            url_for('api.cluster_get', pk=cluster_id),
            headers=self.auth_header
        )

        print('JSON response:', response.json, sep='\n')
        print('get_dict:', self.obj.get_dict(expand=True), sep='\n')

        assert response.json == self.obj.get_dict(expand=True)

    @pytest.mark.parametrize('cluster_id,status_code', [
        (uuid4(), 404),
        ('wrong-uuid', 404),
    ])
    def test_object_not_found(self, cluster_id, status_code):
        response = self.client.get(
            url_for('api.cluster_get', pk=cluster_id),
            headers=self.auth_header
        )
        assert response.status_code == status_code

    def test_cluster_status_returns(self):
        cluster_id = self.obj.id

        response = self.client.get(
            url_for('api.cluster_status', pk=cluster_id),
            headers=self.auth_header
        )
        assert response.status_code == 200

        rj = response.json

        assert 'deployments' in rj
        assert 'nodes' in rj
        assert 'nodes_pods' in rj
        assert 'pods' in rj
        assert 'services' in rj
        assert 'version' in rj
        assert 'git_version' in rj['version']
        assert 'platform' in rj['version']

    @pytest.mark.parametrize('cluster_id,status_code', [
        (uuid4(), 404),
        ('sdfsdfabc123', 404),
    ])
    @pytest.mark.parametrize('url', [
        'cluster_status',
        'cluster_kubeconfig'
    ])
    def test_cluster_status_404(self, url, cluster_id, status_code):
        url = url_for('api.{}'.format(url), pk=cluster_id)
        response = self.client.get(url, headers=self.auth_header)

        assert response.status_code == status_code

    def test_kubeconfig(self):

        url = url_for('api.cluster_kubeconfig', pk=self.obj.id)
        response = self.client.get(url, headers=self.auth_header)
        assert response.json == self.obj.kubeconfig

    def test_topology_data_format(self):

        url = url_for('api.cluster_topology_data', pk=self.obj.id)
        response = self.client.get(url, headers=self.auth_header)

        assert isinstance(response.json, dict)

        assert 'items' in response.json
        assert 'kinds' in response.json
        assert 'relations' in response.json

    def test_create(self, provisioner):
        provisioner.save()

        post_data = {
            'name': 'Testing cluster',
            'provisioner': 'Provisioner:{}'.format(provisioner.id),
        }

        response = self.client.post(
            url_for('api.cluster_create'),
            data=json.dumps(post_data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200

        assert 'id' in response.json
        assert response.json['name'] == post_data['name']
        assert response.json['provisioner'] == provisioner.get_dict()

    def test_provision_after_create(self, provisioner, monkeypatch):
        provisioner.save()

        def fake_provision(self, *args, **kwargs):
            self.cluster.name = 'Provisioned'
            self.cluster.save()

            return True, None

        monkeypatch.setattr(provisioner.get_engine_cls(), 'provision', fake_provision)

        post_data = {
            'name': 'Testing cluster',
            'provisioner': 'Provisioner:{}'.format(provisioner.id),
        }

        response = self.client.post(
            url_for('api.cluster_create'),
            data=json.dumps(post_data),
            headers=self.auth_header,
            content_type='application/json',
        )

        object_id = response.json['id']
        obj = self.obj.__class__.load(self.namespace, object_id)

        assert response.status_code == 200
        assert obj.name == 'Provisioned'

    def test_provision_failed(self, provisioner, monkeypatch):
        provisioner.save()

        def fake_provision(self, *args, **kwargs):
            return False, 'Testing msg'

        monkeypatch.setattr(provisioner.get_engine_cls(), 'provision', fake_provision)

        post_data = {
            'name': 'Testing cluster',
            'provisioner': 'Provisioner:{}'.format(provisioner.id),
        }

        response = self.client.post(
            url_for('api.cluster_create'),
            data=json.dumps(post_data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 500

    def test_return_400_missing_json(self):
        response = self.client.post(
            url_for('api.cluster_create'),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 400

    @pytest.mark.parametrize('data,code,content_type', [
        (json.dumps({'none': 'anything'}), 500, 'application/json'),
        ('abc', 400, 'text/plain'),
    ])
    def test_error_codes(self, data, code, content_type):
        response = self.client.post(
            url_for('api.cluster_create'),
            data=data,
            headers=self.auth_header,
            content_type=content_type,
        )

        assert response.status_code == code
