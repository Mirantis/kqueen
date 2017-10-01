from kqueen.kubeapi import KubernetesAPI

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
