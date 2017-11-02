from .etcd import EtcdBackend
import pytest


class TestEtcdClient:
    @pytest.fixture(autouse=True)
    def prepare(self, monkeypatch):
        self.set_vars = {
            'KQUEEN_ETCD_HOST': 'etcd-server',
            'KQUEEN_ETCD_PORT': '1234',
        }

        for name, value in self.set_vars.items():
            monkeypatch.setenv(name, value)

    def test_config_fields(self):
        orm = EtcdBackend()
        assert orm.client.host == self.set_vars['KQUEEN_ETCD_HOST']
        assert orm.client.port == int(self.set_vars['KQUEEN_ETCD_PORT'])
