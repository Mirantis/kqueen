from .utils import current_config
from .utils import select_file

import pytest

config_file_default = 'config/dev.py'
config_envvar = 'KQUEEN_CONFIG_FILE'

file_parametrization = [
    ('/tmp/test.py', '/tmp/test.py'),
    (None, config_file_default),
    ('', config_file_default),
]


class TestSelectConfig:
    @pytest.mark.parametrize('config_file,req', file_parametrization)
    def test_select_config(self, config_file, req):
        assert select_file(config_file) == req

    @pytest.mark.parametrize('config_file,req', file_parametrization)
    def test_select_config_from_envvar(self, monkeypatch, config_file, req):
        monkeypatch.setenv(config_envvar, config_file)
        assert select_file() == req


class TestCurrentConfig:
    @pytest.mark.parametrize('config_file', [
        'config/dev.py',
        'config/test.py',
    ])
    def test_current_config(self, config_file):
        config = current_config(config_file)

        assert config.source_file == select_file(config_file)


class TestConfigFromEnv:
    @pytest.mark.parametrize('name,value', [
        ('KQUEEN_DUMMY', '123'),
        ('KQUEEN_ETCD_HOST', '4001'),
    ])
    def test_env_var(self, monkeypatch, name, value):
        monkeypatch.setenv(name, value)
        config = current_config()

        config_key_name = name[7:]

        assert config.get(config_key_name) == value
        assert config[config_key_name] == value
