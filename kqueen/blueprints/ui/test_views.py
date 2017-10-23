from flask import url_for
from .views import inject_username
from kqueen.models import User

import pytest


@pytest.mark.parametrize('view,values', [
    ('ui.index', {}),
    ('ui.catalog', {}),
    ('ui.provisioner_create', {'provisioner_id': 1}),
    ('ui.provisioner_delete', {'provisioner_id': 1}),
    ('ui.cluster_detail', {'cluster_id': 1}),
])
def test_login_required(client, view, values):
    response = client.get(url_for(view, **values))

    assert response.status_code == 302


def test_index(client_login):
    response = client_login.get(url_for('.index'))
    assert response.status_code == 200


def test_logout(client_login):
    response = client_login.get(url_for('.logout'))
    assert response.status_code == 302
    assert response.headers['Location'].endswith(url_for('.index'))


def test_inject_username_empty(monkeypatch):
    def fake_load(self, *args, **kwargs):
        raise Exception('Fake error')

    monkeypatch.setattr(User, 'load', fake_load)

    injection = inject_username()
    assert injection['username'] == ''
