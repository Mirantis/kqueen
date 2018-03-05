from . import common
from .ldap import LDAPAuth
from .local import LocalAuth

import pytest
import os

@pytest.mark.parametrize('name, result',
                         [('ldap', LDAPAuth),
                          ('local', LocalAuth)
                          ])
def test_get_auth_instance(name, result):
    os.environ['KQUEEN_CONFIG_FILE'] = 'config/test.py'
    auth_instance = common.get_auth_instance(name)
    assert isinstance(auth_instance, result)
    del os.environ['KQUEEN_CONFIG_FILE']


def test_raises_unknown_engine_class():
    with pytest.raises(Exception, match=r'Authentication engine class name is not provided.'):
        common.get_auth_instance('non-existent')

#TODO: add more tests
