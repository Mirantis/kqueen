from . import common
from .ldap import LDAPAuth
from .local import LocalAuth

import pytest


@pytest.mark.parametrize('name, result',
                         [('ldap', LDAPAuth),
                          ('local', LocalAuth)
                          ])
def test_get_auth_instance(name, result):
    auth_instance = common.get_auth_instance(name)
    assert isinstance(auth_instance, result)


def test_raises_unknown_engine_class():
    with pytest.raises(Exception, match=r'Authentication type is set to non-existent'):
        common.get_auth_instance('non-existent')

# TODO: add more tests
