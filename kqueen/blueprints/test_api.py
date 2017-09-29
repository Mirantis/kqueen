from flask import url_for
from kqueen.models import Cluster
from uuid import uuid4

import pytest


@pytest.fixture
def cluster():
    create_kwargs = {
        'name': 'mycluster',
        'provisioner': 'Jenkins',
        'state': 'failed',
    }
    return Cluster.create(**create_kwargs)


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

