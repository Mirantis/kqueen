from kqueen.models import Cluster
from kqueen.storages.etcd import Field
from kqueen.storages.etcd import Model

import pytest
import yaml
import subprocess


class TestModelMethods:
    @pytest.mark.parametrize('model_class,req', [
        (Model, 'model'),
        (Cluster, 'cluster'),
    ])
    def test_get_model_name(self, model_class, req):
        model_name = model_class.get_model_name()

        assert model_name == req


class TestClusterModel:
    def test_create(self, cluster):
        assert cluster.validate()
        assert cluster.save()

    def test_load(self, cluster):
        cluster.save()

        get_id = cluster.id
        print(get_id)

        loaded = Cluster.load(get_id)
        assert loaded == cluster
        assert hasattr(loaded, '_key'), 'Loaded object is missing _key'

    def test_id_generation(self, provisioner):
        provisioner.save(check_status=False)

        empty = Cluster(name='test', provisioner=provisioner)
        empty.save()

    def test_added_key(self, cluster):
        """Test _key is added after saving"""
        cluster.id = None

        assert not hasattr(cluster, '_key')

        cluster.save()
        assert hasattr(cluster, '_key'), 'Saved object is missing _key'

    def test_exists(self, cluster):
        assert not Cluster.exists(cluster.id)
        cluster.save()
        assert Cluster.exists(cluster.id)

    def test_get_db_key_missing(self, cluster):
        cluster.id = None

        with pytest.raises(Exception, match=r'Missing object id'):
            cluster.get_db_key()

    def test_list_with_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list()
        assert str(cluster.id) in loaded

    def test_list_without_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list(return_objects=False)
        assert str(cluster.id) in loaded
        for o_name, o in loaded.items():
            assert o is None

    def test_status(self, cluster):
        cluster.save()
        status = cluster.status()

        # TODO: add tests for content
        assert isinstance(status, dict)
        assert 'addons' in status

    def test_kubeconfig_is_dict(self, cluster):
        cluster.save()

        assert isinstance(cluster.kubeconfig, dict)

    def test_kubeconfig_load_is_dict(self, cluster):
        cluster.save()

        loaded = Cluster.load(cluster.id)
        assert isinstance(loaded.kubeconfig, dict), 'Loaded kubeconfig is not dict'


class TestFieldCompare:
    def setup(self):
        self.first = Field()
        self.first.set_value('abc')
        self.second = Field()
        self.second.set_value('def')

    def test_compare(self):
        assert self.first != self.second
        assert self.first != 'abc123'

    def test_compare_empty(self):
        empty = Field()

        assert not self.first.empty()
        assert empty.empty()


class TestApply:
    def test_kubeconfig_file(self, cluster):
        cluster.save()

        kubeconfig = cluster.get_kubeconfig_file()
        assert open(kubeconfig, 'r').read() == yaml.dump(cluster.kubeconfig)

    def test_kubeconfig_recycled(self, cluster):
        cluster.save()

        assert not hasattr(cluster, 'kubeconfig_path')
        kubeconfig = cluster.get_kubeconfig_file()

        assert hasattr(cluster, 'kubeconfig_path')
        assert kubeconfig == cluster.get_kubeconfig_file()

    def test_apply(self, cluster, monkeypatch):
        req_cmd = 'kubectl --kubeconfig {} apply -f'.format(cluster.get_kubeconfig_file())

        class FakeRun:
            stdout = 'no stdout'
            returncode = 0

            def __init__(self, cmd, **kwargs):
                self.cmd = cmd
                self.kwargs = kwargs

        def fake_run(cmd, **kwargs):
            return FakeRun(cmd, **kwargs)

        monkeypatch.setattr(subprocess, 'run', fake_run)

        text = """kind: Service
apiVersion: v1
metadata:
  name: my-service
spec:
  selector:
    app: MyApp
  ports:
  - protocol: TCP
    port: 80
    targetPort: 9376
"""

        run = cluster.apply(text)
        cmd = ' '.join(run.cmd)
        assert cmd.startswith(req_cmd)
