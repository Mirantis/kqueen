from .helpers import get_object
from kqueen.conftest import cluster
from kqueen.conftest import user
from kqueen.storages.exceptions import BackendError

import pytest


class TestGetObject:
    def setup(self):
        self.obj = cluster()
        self.obj.save()
        self.user = user()

    def test_get_objects(self):
        obj = get_object(self.obj.__class__, self.obj.id, self.user)

        assert obj.get_dict(True) == self.obj.get_dict(True)

    @pytest.mark.parametrize('bad_user', [
        'None',
        '',
        None,
        {},
    ])
    def test_get_object_malformed_user(self, bad_user):
        with pytest.raises(BackendError, match='Missing namespace for class'):
            get_object(self.obj.__class__, self.obj.id, bad_user)
