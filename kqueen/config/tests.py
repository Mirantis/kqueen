from kqueen.config.utils import kqueen_config
from kqueen.server import create_app
from .base import BaseConfig

import pytest

config_envvar = 'KQUEEN_CONFIG_FILE'
config_file_default = 'config/test.py'

file_parametrization = [
    ('/tmp/test.py', '/tmp/test.py'),
    (None, config_file_default),
    ('', config_file_default),
]


class TestConfigFromEnv:
    @pytest.mark.parametrize('name,value', [
        ('KQUEEN_DUMMY', '123'),
        ('KQUEEN_ETCD_HOST', '4001'),
    ])
    def test_env_var(self, monkeypatch, name, value):
        monkeypatch.setenv(name, value)

        config_key_name = name[7:]

        assert kqueen_config.get(config_key_name) == value

    def test_env_var_in_app(self, monkeypatch):
        monkeypatch.setenv('KQUEEN_DUMMY', '123')

        app = create_app()

        assert app.config.get('DUMMY') == '123'


class TestBaseFunction:
    def setup(self):
        self.cl = BaseConfig

    def test_to_dict(self):
        dicted = self.cl.to_dict()

        assert isinstance(dicted, dict)
        assert dicted['DEBUG'] is False

    def test_get_regular(self):
        assert self.cl.get('DEBUG') is False

    def test_get_default(self):
        assert self.cl.get('NONEXISTING', 123) == 123
