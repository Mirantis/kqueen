from kqueen.kubeapi import KubernetesAPI
from pprint import pprint

import pytest


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
