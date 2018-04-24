from .helpers import get_object

from kqueen.storages.exceptions import BackendError

import pytest


@pytest.mark.usefixtures('cluster', 'user')
class TestGetObject:

    def test_get_objects(self, cluster, user):
        cluster.save()
        obj = get_object(cluster.__class__, cluster.id, user)

        assert obj.get_dict(True) == obj.get_dict(True)

    @pytest.mark.parametrize('bad_user', [
        'None',
        '',
        None,
        {},
    ])
    def test_get_object_malformed_user(self, cluster, bad_user):
        with pytest.raises(BackendError, match='Missing namespace for class'):
            get_object(cluster.__class__, cluster.id, bad_user)
