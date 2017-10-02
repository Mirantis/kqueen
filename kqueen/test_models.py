from kqueen.models import Cluster
from kqueen.storages.etcd import Field
from kqueen.storages.etcd import Model
from pprint import pprint

import pytest


class TestModelMethods:
    @pytest.mark.parametrize('model_class,req', [
        (Model, 'model'),
        (Cluster, 'cluster'),
    ])
    def test_get_model_name(self, model_class, req):
        model_name = model_class.get_model_name()

        assert model_name == req

    def test_get_db_prefix(self):
        model_class = Cluster
        req = '/kqueen/obj/default/cluster/'

        assert model_class.get_db_prefix() == req


class TestClusterModel:
    def test_create(self, cluster):
        assert cluster.validate()
        assert cluster.save()

    def test_load(self, cluster):
        get_id = cluster.id
        cluster.save()

        loaded = Cluster.load(get_id)
        assert loaded == cluster
        assert hasattr(loaded, '_key'), 'Loaded object is missing _key'

    def test_id_generation(self):
        empty = Cluster()
        empty.save()

    def test_added_key(self, cluster):
        """Test _key is added after saving"""
        cluster.id.set_value(None)

        assert not hasattr(cluster, '_key')

        cluster.save()
        assert hasattr(cluster, '_key'), 'Saved object is missing _key'

    def test_exists(self, cluster):
        assert not Cluster.exists(cluster.id)
        cluster.save()
        assert Cluster.exists(cluster.id)

    def test_get_db_key_missing(self, cluster):
        cluster.id.set_value(None)

        with pytest.raises(Exception, match=r'Missing object id'):
            cluster.get_db_key()

    def test_list_with_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list()
        assert str(cluster.id) in loaded

    def test_list_without_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list(return_objects=False)
        assert str(cluster.id) in loaded
        for o_name, o in loaded.items():
            assert o is None

    def test_status(self, cluster):
        cluster.save()
        status = cluster.status()
        pprint(status)

        assert isinstance(status, dict)
        # TODO: add tests for content

    def test_kubeconfig_is_dict(self, cluster):
        cluster.save()

        assert isinstance(cluster.kubeconfig.value, dict)

    def test_kubeconfig_load_is_dict(self, cluster):
        cluster.save()

        loaded = Cluster.load(cluster.id.value)
        assert isinstance(loaded.kubeconfig.value, dict), 'Loaded kubeconfig is not dict'


class TestFieldCompare:
    def setup(self):
        self.first = Field()
        self.first.set_value('abc')
        self.second = Field()
        self.second.set_value('def')

    def test_compare(self):
        assert self.first != self.second

    def test_compare_empty(self):
        empty = Field()

        assert not self.first.empty()
        assert empty.empty()
