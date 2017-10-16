from flask import url_for
from kqueen.models import Provisioner
from .forms import _get_provisioners

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


class TestProvisionerForm:
    def test_get_provisioners(self):
        provisioners = list(Provisioner.list(return_objects=True).values())
        choices = []

        # create list of choices
        for provisioner in provisioners:
            choices.append((provisioner.id, provisioner.name))

        assert _get_provisioners() == choices
