from .helpers import get_object

from kqueen.storages.exceptions import BackendError
from kqueen.conftest import ClusterFixture

import pytest


@pytest.mark.usefixtures('user')
class TestGetObject:
    def setup(self):
        self.test_cluster = ClusterFixture()
        self.cluster = self.test_cluster.obj
        self.cluster.save()

    def teardown(self):
        self.test_cluster.destroy()

    def test_get_objects(self, user):

        obj = get_object(self.cluster.__class__,
                         self.cluster.id, user)

        assert obj.get_dict(True) == obj.get_dict(True)

    @pytest.mark.parametrize('bad_user', [
        'None',
        '',
        None,
        {},
    ])
    def test_get_object_malformed_user(self, bad_user):
        with pytest.raises(BackendError, match='Missing namespace for class'):
            get_object(self.cluster.__class__, self.cluster.id, bad_user)
