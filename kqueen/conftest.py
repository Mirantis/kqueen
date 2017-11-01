"""Configuration and fixtures for pytest."""
from faker import Faker
from flask_jwt import JWT
from kqueen.auth import authenticate
from kqueen.auth import identity
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from kqueen.server import create_app

import json
import pytest
import uuid
import yaml

config_file = 'config/test.py'
fake = Faker()


@pytest.fixture
def app():
    """Prepare app with JWT."""
    app = create_app(config_file=config_file)
    JWT(app, authenticate, identity)
    return app


@pytest.fixture
def cluster():
    """Create cluster with manual provisioner."""
    _uuid = uuid.uuid4()

    prov = Provisioner(
        name='Fixtured provisioner',
        engine='kqueen.engines.ManualEngine',
    )
    prov.save(check_status=False)

    create_kwargs = {
        'id': _uuid,
        'name': 'Name for cluster {}'.format(_uuid),
        'provisioner': prov,
        'state': 'deployed',
        'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
    }

    return Cluster.create(**create_kwargs)


@pytest.fixture
def provisioner():
    """Create dummy manual provisioner."""
    create_kwargs = {
        'name': 'Fixtured provisioner',
        'engine': 'kqueen.engines.ManualEngine',
    }

    return Provisioner.create(**create_kwargs)


@pytest.fixture
def auth_header(client):
    """
    Get JWT access token and convert it to HTTP header.

    Args:
        client: Flask client

    Returns:
        dict: {'Authorization': 'JWT access_token'}

    """
    _user = user()
    data = {
        'username': _user.username,
        'password': _user.password
    }
    response = client.post(
        '/api/v1/auth',
        data=json.dumps(data),
        content_type='application/json')

    return {'Authorization': 'JWT {}'.format(response.json['access_token'])}


@pytest.fixture
def organization():
    """Prepare organization object."""
    organization = Organization(
        name='DemoOrg',
        namespace='demoorg',
    )
    organization.save()

    return organization


@pytest.fixture
def user():
    """Prepare user object."""
    profile = fake.simple_profile()
    user = User(
        username=profile['username'],
        password=fake.password(),
        organization=organization(),
    )
    user.save()

    return user
