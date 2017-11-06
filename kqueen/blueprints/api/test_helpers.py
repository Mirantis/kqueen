from .helpers import get_object
from kqueen.conftest import cluster
from kqueen.conftest import user

import pytest


class TestGetObject:
    def setup(self):
        self.obj = cluster()
        self.obj.save()
        self.user = user()

    def test_get_objects(self):
        obj = get_object(self.obj.__class__, self.obj.id, user=self.user)

        assert obj == self.obj

    @pytest.mark.parametrize('bad_user', [
        'None',
        '',
        None,
        {},
    ])
    def test_get_object_malformed_user(self, bad_user):
        get_object(self.obj.__class__, self.obj.id, user=bad_user)
