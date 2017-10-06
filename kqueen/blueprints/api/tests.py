from flask import url_for
from uuid import uuid4

import pytest


def test_root(client):
    response = client.get(url_for('api.index'))

    assert response.json == {'response': 'Gutten tag!'}


class TestClusterList:
    def test_cluster_list(self, cluster, client):
        cluster.save()

        response = client.get(url_for('api.cluster_list'))
        assert cluster.get_dict() in response.json


class TestClusterDetails:
    def test_cluster_detail(self, cluster, client):
        cluster.save()
        cluster_id = cluster.id

        response = client.get(url_for('api.cluster_detail', cluster_id=cluster_id))
        assert response.json == cluster.get_dict()

    @pytest.mark.parametrize('cluster_id', [
        uuid4(),
        'wrong-uuid',
    ])
    def test_object_not_found(self, client, cluster_id):
        response = client.get(url_for('api.cluster_detail', cluster_id=cluster_id))
        assert response.status_code == 404


class TestClusterStatus:
    def test_cluster_status_returns(self, cluster, client):
        cluster.save()
        cluster_id = cluster.id

        response = client.get(url_for('api.cluster_status', cluster_id=cluster_id))
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

    @pytest.mark.parametrize('cluster_id', [
        uuid4(),
        'abc123'
    ])
    @pytest.mark.parametrize('url', [
        'cluster_status',
        'cluster_kubeconfig'
    ])
    def test_cluster_status_404(self, client, url, cluster_id):
        url = url_for('api.{}'.format(url), cluster_id=cluster_id)
        response = client.get(url)
        assert response.status_code == 404


class TestClusterKubeconfig:
    def test_kubeconfig(self, cluster, client):
        cluster.save()

        url = url_for('api.cluster_kubeconfig', cluster_id=cluster.id)
        response = client.get(url)
        assert response.json == cluster.kubeconfig.value
