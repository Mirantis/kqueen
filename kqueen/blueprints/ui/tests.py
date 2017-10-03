from flask import url_for

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
