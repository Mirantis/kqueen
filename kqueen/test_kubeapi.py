from kqueen.kubeapi import KubernetesAPI
from kubernetes.client.rest import ApiException
from pprint import pprint as print

import pytest
import yaml

def fake_raise(exc):
    def fn(self, *args, **kwargs):
        raise exc

    return fn


class TestKubeApi:
    def test_missing_cluster_param(self):
        with pytest.raises(ValueError, match='Missing parameter cluster'):
            KubernetesAPI()

    def test_get_kubeconfig(self, cluster):
        """Test get_kubeconfig returns YAML"""

        cluster.save()
        api = KubernetesAPI(cluster=cluster)
        print(api.get_kubeconfig_file())

    def test_init(self, cluster):
        cluster.save()

        api = KubernetesAPI(cluster=cluster)

        assert hasattr(api, 'cluster')

    def test_version(self, cluster):
        api = KubernetesAPI(cluster=cluster)

        version = api.get_version()
        print(version)

        assert isinstance(version, dict)
        assert 'git_version' in version
        assert 'platform' in version

    def test_list_nodes(self, cluster):
        api = KubernetesAPI(cluster=cluster)
        nodes = api.list_nodes()

        assert isinstance(nodes, list)

    @pytest.mark.parametrize('method_name', [
        'list_nodes',
        'list_pods',
        'list_pods_by_node',
        'count_pods_by_node',
        'resources_by_node',
        'list_services',
        'list_deployments',
    ])
    def test_raise_apiexception(self, cluster, monkeypatch, method_name):
        monkeypatch.setattr(KubernetesAPI, method_name, fake_raise(ApiException))

        api = KubernetesAPI(cluster=cluster)
        method = getattr(api, method_name)

        with pytest.raises(ApiException):
            method()

    def test_pod_list(self, cluster):
        api = KubernetesAPI(cluster=cluster)
        pods = api.list_pods()

        assert isinstance(pods, list)

    def test_list_pods_by_node(self, cluster):
        api = KubernetesAPI(cluster=cluster)

        pods = api.list_pods_by_node()

        assert isinstance(pods, dict)

    def test_list_services(self, cluster):
        api = KubernetesAPI(cluster=cluster)

        services = api.list_services()
        assert isinstance(services, list)

    def test_list_deployments(self, cluster):
        api = KubernetesAPI(cluster=cluster)

        deployments = api.list_deployments()
        assert isinstance(deployments, list)

    def test_resource_by_node(self, cluster):
        api = KubernetesAPI(cluster=cluster)

        resources = api.resources_by_node()
        assert isinstance(resources, dict)

    def test_resource_by_node_faked(self, cluster, monkeypatch):
        def fake_list_pods(self):
            with open('kqueen/fixtures/testdata_list_pods_by_node.yml', 'r') as stream:
                data_loaded = yaml.load(stream)
            return data_loaded

        monkeypatch.setattr(KubernetesAPI, 'list_pods_by_node', fake_list_pods)

        api = KubernetesAPI(cluster=cluster)
        resources = api.resources_by_node()

        req = {
            'minion1': {
                'limits': {'cpu': 5.0, 'memory': 2147483648.0},
                'requests': {'cpu': 1.1, 'memory': 512102400.0}
            }
        }
        print(resources)

        assert resources == req
