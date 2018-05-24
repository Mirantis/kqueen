"""Configuration and fixtures for pytest."""
from kqueen.config import current_config
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from kqueen.server import create_app

import datetime
import etcd
import faker
import json
import pytest
import random
import string
import uuid
import yaml

config = current_config()
fake = faker.Faker()
current_app = None


class ClusterFixture:
    def __init__(self, test_provisioner=None, test_user=None):
        test_user = test_user if test_user is not None else UserFixture()

        if not test_provisioner:
            test_provisioner = ProvisionerFixture(test_user=test_user)
        self.test_provisioner = test_provisioner

        owner = test_user.obj
        provisioner = self.test_provisioner.obj

        provisioner.state = config.get('PROVISIONER_OK_STATE')
        provisioner.save(check_status=False)

        _uuid = uuid.uuid4()
        create_kwargs = {
            'id': _uuid,
            'name': 'Name for cluster {}'.format(_uuid),
            'provisioner': provisioner,
            'state': config.get('CLUSTER_UNKNOWN_STATE'),
            'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
            'created_at': datetime.datetime.utcnow().replace(microsecond=0),
            'owner': owner
        }
        self.obj = Cluster.create(owner.namespace, **create_kwargs)

    def destroy(self):
        try:
            self.obj.delete()
            self.test_provisioner.destroy()
        except Exception:
            # Provisioner may be already deleted
            pass


class ProvisionerFixture:
    def __init__(self, test_user=None):
        if test_user is None:
            test_user = UserFixture()
        self.test_user = test_user

        owner = test_user.obj
        create_kwargs = {
            'name': 'Fixtured provisioner',
            'engine': 'kqueen.engines.ManualEngine',
            'owner': owner
        }
        self.obj = Provisioner.create(owner.namespace, **create_kwargs)

    def destroy(self):
        try:
            self.obj.delete()
            self.test_user.destroy()
        except Exception:
            # Provisioner may be already deleted
            pass


class UserFixture:
    def __init__(self, namespace=None):
        profile = fake.simple_profile()
        self.test_org = OrganizationFixture(namespace)
        user = User.create(
            None,
            username=profile['username'],
            password=profile['username'] + 'password',
            organization=self.test_org.obj,
            role='superadmin',
            active=True
        )
        user.save(validate=False)
        self.obj = user

    def destroy(self):
        try:
            self.obj.delete()
            self.test_org.destroy()
        except Exception:
            # User be may already deleted
            pass


class OrganizationFixture:
    def __init__(self, name=None):
        """Prepare organization object."""
        if not name:
            name = ''.join(random.choice(string.ascii_letters) for _ in range(8))
        organization = Organization(
            None,
            name=name,
            namespace=name
        )
        organization.save(validate=False)

        self.obj = organization

    def destroy(self):
        try:
            self.obj.delete()
        except Exception:
            # Organization be may already deleted
            pass


class AuthHeader:
    def __init__(self, test_user=None):
        self.user = test_user if test_user is not None else UserFixture()

    def get(self, client):
        """
        Get JWT access token and convert it to HTTP header.

        Args:
            client: Flask client

        Returns:
            dict: {'Authorization': 'JWT access_token'}

        """
        _user = self.user.obj
        token = get_auth_token(client, _user)

        return {
            'Authorization': '{token_prefix} {token}'.format(
                token_prefix=config.get('JWT_AUTH_HEADER_PREFIX'),
                token=token,
            ),
            'X-Test-Namespace': _user.namespace,
            'X-User': str(_user.id),
        }

    def destroy(self):
        self.user.destroy()


class UserWithNamespaceFixture:
    def __init__(self):
        self.test_org = OrganizationFixture()
        org = self.test_org.obj

        namespace = fake.user_name()
        org.namespace = namespace
        org.save()

        self.test_user = UserFixture()
        _user = self.test_user.obj
        _user.organization = org
        _user.save()
        self.obj = _user

    def destroy(self):
        self.test_org.destroy()
        self.test_user.destroy()


@pytest.fixture(autouse=True, scope='session')
def app():
    """Prepare app."""
    global current_app
    current_app = create_app()
    current_app.testing = True

    return current_app


@pytest.fixture(autouse=True, scope='class')
def etcd_setup():
    global current_app
    try:
        current_app.db.client.delete(current_app.config['ETCD_PREFIX'], recursive=True)
    except etcd.EtcdKeyNotFound:
        pass


@pytest.fixture
def cluster():
    """Create cluster with manual provisioner."""
    test_cluster = ClusterFixture()
    yield test_cluster.obj
    test_cluster.destroy()


@pytest.fixture
def provisioner():
    """Create dummy manual provisioner."""
    test_provisioner = ProvisionerFixture()
    test_provisioner.obj.save()
    yield test_provisioner.obj
    test_provisioner.destroy()


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


@pytest.fixture(scope='class', autouse=True)
def user():
    """Prepare user object."""
    with current_app.app_context():
        test_org = OrganizationFixture()
        profile = fake.simple_profile()
        user = User.create(
            None,
            username=profile['username'],
            password=profile['username'] + 'password',
            organization=test_org.obj,
            role='superadmin',
            active=True
        )

        user.save()
        yield user
        try:
            user.delete()
            test_org.destroy()
        except Exception:
            # objects may be already deleted
            pass
