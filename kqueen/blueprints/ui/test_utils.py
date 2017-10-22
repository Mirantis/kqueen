from .utils import status_for_cluster_detail

import pytest
import json

@pytest.fixture
def cluster_status():
    with open('kqueen/fixtures/test_cluster_status.json', 'r') as stream:
        data_loaded = json.load(stream)

    return data_loaded

class TestNodes:
    def setup(self):
        self.status = status_for_cluster_detail(cluster_status())
        self.nodes = self.status['nodes']

    def test_names(self):
        names = list(map(lambda i: i['name'], self.nodes))
        req = [
            'ip-10-0-10-10.us-west-2.compute.internal',
            'ip-10-0-10-12.us-west-2.compute.internal',
            'ip-10-0-10-13.us-west-2.compute.internal',
            'ip-10-0-10-30.us-west-2.compute.internal',
            'ip-10-0-10-95.us-west-2.compute.internal'
        ]
        assert names == req

    @pytest.mark.parametrize('field', [
        'name',
        'ip',
        'os',
        'status',
        'size',
        'pods',
    ])
    def test_field(self, field):
        for node in self.nodes:
            assert field in node
            assert node.get(field)

class TestDeployments:
    def setup(self):
        self.status = status_for_cluster_detail(cluster_status())
        self.deployments = self.status['deployments']

    def test_names(self):
        names = list(map(lambda i: i['name'], self.deployments))
        req = [
            'app-load-1',
            'app-load-10',
            'app-load-11',
            'app-load-12',
            'app-load-13',
            'app-load-14',
            'app-load-15',
            'app-load-16',
            'app-load-17',
            'app-load-18',
            'app-load-19',
            'app-load-2',
            'app-load-20',
            'app-load-3',
            'app-load-4',
            'app-load-5',
            'app-load-6',
            'app-load-7',
            'app-load-8',
            'app-load-9',
            'flask',
            'redis',
            'kube-dns',
            'kube-dns-autoscaler',
            'kubernetes-dashboard'
        ]

        assert names == req

    @pytest.mark.parametrize('field', [
        'name',
        'namespace',
        'replicas',
        'containers',
    ])
    def test_node_field(self, field):
        for deployment in self.deployments:
            assert field in deployment
            assert deployment.get(field)

class TestServices:
    def setup(self):
        self.status = status_for_cluster_detail(cluster_status())
        self.services = self.status['services']

    def test_name(self):
        names = list(map(lambda i: i['name'], self.services))
        req = [
            'app-load-1',
            'app-load-10',
            'app-load-11',
            'app-load-12',
            'app-load-13',
            'app-load-14',
            'app-load-15',
            'app-load-16',
            'app-load-17',
            'app-load-18',
            'app-load-19',
            'app-load-2',
            'app-load-20',
            'app-load-3',
            'app-load-4',
            'app-load-5',
            'app-load-6',
            'app-load-7',
            'app-load-8',
            'app-load-9',
            'demo-kqueen',
            'flask',
            'kubernetes',
            'mongodb',
            'monocular',
            'my-service',
            'redis',
            'registry',
            'sonobyoy',
            'tmpl',
            'kube-dns',
            'kubernetes-dashboard'
        ]

        assert names == req

    @pytest.mark.parametrize('field', [
        'name',
        'namespace',
        'cluster_ip',
        'ports',
        'external_ip',
    ])
    def test_node_field(self, field):
        for service in self.services:
            assert field in service


class TestEmptyStatusForCluster:
    def setup(self):
        self.status = status_for_cluster_detail({})

    @pytest.mark.parametrize('key', ['services', 'addons', 'nodes', 'deployments', 'overview'])
    def test_status_for_cluster_detail_empty(self, key):
        assert key in self.status
