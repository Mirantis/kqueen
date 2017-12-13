"""Configuration and fixtures for pytest."""
from faker import Faker
from kqueen.config import current_config
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from kqueen.server import create_app

import datetime
import etcd
import json
import pytest
import uuid
import yaml

config_file = 'config/test.py'
config = current_config()
fake = Faker()


@pytest.fixture(autouse=True, scope='session')
def app():
    """Prepare app."""
    app = create_app()
    app.testing = True

    return app


@pytest.fixture(autouse=True, scope='session')
def etcd_setup():
    _app = create_app()

    try:
        _app.db.client.delete(_app.config['ETCD_PREFIX'], recursive=True)
    except etcd.EtcdKeyNotFound:
        pass


@pytest.fixture
def cluster():
    """Create cluster with manual provisioner."""
    _uuid = uuid.uuid4()
    _user = user()

    prov = Provisioner(
        _user.namespace,
        name='Fixtured provisioner',
        engine='kqueen.engines.ManualEngine',
        owner=_user
    )
    prov.save(check_status=False)

    create_kwargs = {
        'id': _uuid,
        'name': 'Name for cluster {}'.format(_uuid),
        'provisioner': prov,
        'state': 'deployed',
        'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
        'created_at': datetime.datetime(2017, 11, 15, 13, 36, 24),
        'owner': _user
    }

    return Cluster.create(_user.namespace, **create_kwargs)


@pytest.fixture
def provisioner():
    """Create dummy manual provisioner."""
    _user = user()

    create_kwargs = {
        'name': 'Fixtured provisioner',
        'engine': 'kqueen.engines.ManualEngine',
        'owner': _user
    }

    return Provisioner.create(_user.namespace, **create_kwargs)


def get_auth_token(_client, _user):
    """
    Acquire token for given user

    Args:
        client: Client connection
        user: User object

    Returns:
        str: Auth token.
    """

    data = {
        'username': _user.username,
        'password': _user.username + 'password'
    }

    response = _client.post(
        '/api/v1/auth',
        data=json.dumps(data),
        content_type='application/json')

    try:
        token = response.json['access_token']
    except KeyError as e:
        raise KeyError('Unable to read access token from response: {}'.format(response.data))

    return token


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
    token = get_auth_token(client, _user)

    return {
        'Authorization': '{token_prefix} {token}'.format(
            token_prefix=config.get('JWT_AUTH_HEADER_PREFIX'),
            token=token,
        ),
        'X-Test-Namespace': _user.namespace,
        'X-User': str(_user),
    }


@pytest.fixture
def organization():
    """Prepare organization object."""
    organization = Organization(
        None,
        name='DemoOrg',
        namespace='demoorg',
    )
    organization.save()

    return organization


@pytest.fixture(scope='class')
def user():
    """Prepare user object."""
    profile = fake.simple_profile()
    user = User.create(
        None,
        username=profile['username'],
        password=profile['username'] + 'password',
        organization=organization(),
        role='superadmin',
        active=True
    )
    user.save()

    return user


@pytest.fixture
def user_with_namespace():

    org = organization()
    org.namespace = fake.user_name()
    org.save()

    _user = user()
    _user.organization = org
    _user.save()

    return _user
