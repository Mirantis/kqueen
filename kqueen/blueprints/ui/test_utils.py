from .utils import status_for_cluster_detail


def test_status_for_cluster_detail_empty():
    status = status_for_cluster_detail({})
    expected_keys = ['services', 'addons', 'nodes', 'deployments', 'overview']
    assert set(expected_keys).issubset(status)
