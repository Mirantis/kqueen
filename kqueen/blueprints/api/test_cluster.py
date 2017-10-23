from flask import url_for
from uuid import uuid4
from kqueen.conftest import cluster
from kqueen.conftest import auth_header

import pytest
import json


@pytest.mark.usefixtures('client_class')
class TestCRUD:
    def get_object(self):
        return cluster()

    def get_resource_type(self):
        return self.obj.__class__.__name__.lower()

    def get_edit_data(self):
        return {'name': 'patched cluster'}

    def get_urls(self):
        return {
            'list': url_for('api.{}_list'.format(self.get_resource_type())),
            'create': url_for('api.{}_create'.format(self.get_resource_type())),
            'read': url_for(
                'api.{}_get'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
            'update': url_for(
                'api.{}_update'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
            'delete': url_for(
                'api.{}_delete'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
        }

    def setup(self):
        self.obj = self.get_object()
        self.auth_header = auth_header(self.client)
        self.urls = self.get_urls()

        self.obj.save()

    def test_list(self):

        response = self.client.get(
            self.urls['list'],
            headers=self.auth_header,
        )

        data = response.json
        print(data)

        assert isinstance(data, list)
        assert len(data) == len(self.obj.__class__.list(return_objects=False))
        assert self.obj.get_dict() in data


    def test_edit(self):
        response = self.client.patch(
            url_for('api.cluster_detail', cluster_id=cluster_id),
            data=json.dumps(self.get_edit_data()),
            headers=auth_header,
        )

        assert response.status_code == 200

        patched = cluster_class.load(cluster_id)
        assert patched.name == patch_data['name']

    def test_delete_cluster(self, cluster, client, auth_header):
        cluster.save()
        cluster_id = cluster.id
        cluster_class = cluster.__class__

        response = client.delete(
            url_for('api.cluster_detail', cluster_id=cluster_id),
            headers=auth_header,
        )

        assert response.status_code == 200
        with pytest.raises(NameError, message='Object not found'):
            cluster_class.load(cluster_id)


class TestClusterDetails:
    def test_cluster_detail(self, cluster, client, auth_header):
        cluster.save()
        cluster_id = cluster.id

        response = client.get(url_for('api.cluster_detail', cluster_id=cluster_id), headers=auth_header)
        assert response.json == cluster.get_dict()

    @pytest.mark.parametrize('cluster_id,status_code', [
        (uuid4(), 404),
        ('wrong-uuid', 400),
    ])
    def test_object_not_found(self, client, cluster_id, auth_header, status_code):
        response = client.get(url_for('api.cluster_detail', cluster_id=cluster_id), headers=auth_header)
        assert response.status_code == status_code


class TestClusterStatus:
    def test_cluster_status_returns(self, cluster, client, auth_header):
        cluster.save()
        cluster_id = cluster.id

        response = client.get(url_for('api.cluster_status', cluster_id=cluster_id), headers=auth_header)
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
        ('sdfsdfabc123', 400),
    ])
    @pytest.mark.parametrize('url', [
        'cluster_status',
        'cluster_kubeconfig'
    ])
    def test_cluster_status_404(self, client, url, cluster_id, auth_header, status_code):
        url = url_for('api.{}'.format(url), cluster_id=cluster_id)
        response = client.get(url, headers=auth_header)
        print(response.__dict__)
        print(response.data)

        assert response.status_code == status_code


class TestClusterKubeconfig:
    def test_kubeconfig(self, cluster, client, auth_header):
        cluster.save()

        url = url_for('api.cluster_kubeconfig', cluster_id=cluster.id)
        response = client.get(url, headers=auth_header)
        assert response.json == cluster.kubeconfig


class TestTopologyData:
    def test_topology_data_format(self, cluster, client, auth_header):
        cluster.save()

        url = url_for('api.cluster_topology_data', cluster_id=cluster.id)
        response = client.get(url, headers=auth_header)

        assert isinstance(response.json, dict)

        assert 'items' in response.json
        assert 'kinds' in response.json
        assert 'relations' in response.json


class TestClusterCreate:
    def setup(self):
        self.url = url_for('api.cluster_list')

    def test_create(self, provisioner, client, auth_header):
        provisioner.save()
        post_data = {
            'name': 'Testing cluster',
            'provisioner': provisioner.id,
        }

        response = client.post(
            self.url,
            data=json.dumps(post_data),
            headers=auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200

        response_dict = json.loads(response.json)
        assert 'id' in response_dict
        assert response_dict['name'] == post_data['name']
        assert response_dict['provisioner'] == provisioner.id

    def test_return_400_missing_json(self, client, auth_header):
        response = client.post(
            self.url,
            headers=auth_header,
            content_type='application/json',
        )

        assert response.status_code == 400

    @pytest.mark.parametrize('data,code,content_type', [
        (json.dumps({'none': 'anything'}), 500, 'application/json'),
        ('abc', 400, 'text/plain'),
    ])
    def test_error_codes(self, client, auth_header, data, code, content_type):
        response = client.post(
            self.url,
            data=data,
            headers=auth_header,
            content_type=content_type,
        )

        assert response.status_code == code
