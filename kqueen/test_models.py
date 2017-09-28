from kqueen.models import Cluster
from kqueen.models import Model
from kqueen.models import Field

import pytest
import uuid


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
    @pytest.fixture
    def cluster(self):
        _uuid = uuid.uuid4()
        create_kwargs = {
            'name': 'mycluster',
            'color': 'red',
            'id': _uuid,
        }

        return Cluster.create(**create_kwargs)

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
