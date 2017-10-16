from flask import current_app
from flask import url_for
from kqueen.models import Cluster
from kqueen.server import create_app

import pytest
import uuid
import yaml

config_file = 'config/test.py'


@pytest.fixture
def app():
    app = create_app(config_file=config_file)
    return app


@pytest.fixture
def cluster():
    _uuid = uuid.uuid4()

    create_kwargs = {
        'id': _uuid,
        'name': 'Name for cluster {}'.format(_uuid),
        'provisioner': 'Jenkins',
        'state': 'deployed',
        'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
    }

    return Cluster.create(**create_kwargs)


@pytest.fixture
def client_login(client):
    client.post(url_for('ui.login'), data={
        'username': current_app.config['USERNAME'],
        'password': current_app.config['PASSWORD'],
    })
    return client
