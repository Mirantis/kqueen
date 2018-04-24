from .etcd import EtcdBackend

import os


class TestEtcdClient:
    def setup(self):
        self.set_vars = {
            'KQUEEN_ETCD_HOST': 'etcd-server',
            'KQUEEN_ETCD_PORT': '1234',
        }
        self.existent = {}
        for name, value in self.set_vars.items():
            if name in os.environ:
                self.existent[name] = os.environ[name]
            os.environ[name] = value

    def test_config_fields(self):
        orm = EtcdBackend()
        assert orm.client.host == self.set_vars['KQUEEN_ETCD_HOST']
        assert orm.client.port == int(self.set_vars['KQUEEN_ETCD_PORT'])

    def teardown(self):
        for name, value in self.existent.items():
            os.environ[name] = value
