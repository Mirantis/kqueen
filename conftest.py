from kqueen.models import Cluster
from kqueen.server import create_app

import pytest
import uuid
import yaml


@pytest.fixture
def app():
    app = create_app()
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
