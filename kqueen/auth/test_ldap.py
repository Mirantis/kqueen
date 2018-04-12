from .ldap import LDAPAuth
from kqueen.models import User
from kqueen.exceptions import ImproperlyConfigured

import pytest


class TestAuthMethod:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.user.username = 'admin'
        self.user.metadata = {}
        self.user.password = ''
        self.user.save()

        self.auth_class = LDAPAuth(uri='ldap://127.0.0.1', admin_dn='cn=admin,dc=example,dc=org', password='heslo123')

    def test_raise_on_missing_creds(self):
        with pytest.raises(Exception, msg='Failed to configure LDAP, please provide valid LDAP credentials'):
            LDAPAuth()

    def test_login_pass(self):
        password = 'heslo123'

        user, error = self.auth_class.verify(self.user, password)

        assert isinstance(user, User)
        assert error is None

    def test_login_bad_pass(self):
        password = 'abc'
        user, error = self.auth_class.verify(self.user, password)

        assert not user
        assert error == 'Failed to validate full-DN. Check CN name and defined password of invited user'

    def test_bad_server(self):
        with pytest.raises(ImproperlyConfigured, msg='Failed to bind connection for Kqueen Read-only user'):
            LDAPAuth(uri='ldap://127.0.0.1:55555', admin_dn='cn=admin,dc=example,dc=org', password='heslo123')
