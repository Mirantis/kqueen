from .ldap import LDAPAuth
from kqueen.models import User

import pytest


class TestAuthMethod:
    @pytest.fixture(autouse=True)
    def setup(self, user):
        self.user = user
        self.user.username = 'admin@example.org'
        self.user.password = ''
        self.user.save()

        self.auth_class = LDAPAuth(uri='ldap://127.0.0.1:389')

    def test_raise_on_missing_uri(self):
        with pytest.raises(Exception, msg='Parameter uri is required'):
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
        assert error == "Invalid LDAP credentials"

    def test_bad_server(self):
        password = 'heslo123'
        auth_class = LDAPAuth(uri="ldap://127.0.0.1:55555")

        user, error = auth_class.verify(self.user, password)
        assert not user
        assert error == "LDAP auth failed, check log for error"

    @pytest.mark.parametrize('email, dn', [
        ('admin@example.org', 'cn=admin,dc=example,dc=org'),
        ('name.surname@mail.example.net', 'cn=name.surname,dc=mail,dc=example,dc=net'),
        ('user', 'cn=user'),
    ])
    def test_email_to_dn(self, email, dn):
        assert self.auth_class._email_to_dn(email) == dn
