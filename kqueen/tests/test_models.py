from datetime import datetime
from datetime import timedelta
from kqueen.config import current_config
from kqueen.engines import __all__ as all_engines
from kqueen.engines import ManualEngine
from kqueen.models import Cluster
from kqueen.models import Provisioner
from kqueen.storages.etcd import Field
from kqueen.storages.etcd import Model

import pytest
import subprocess
import yaml

config = current_config()


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
        validation, _ = cluster.validate()

        assert validation
        assert cluster.save()

    def test_load(self, cluster):
        cluster.save()

        get_id = cluster.id

        loaded = Cluster.load(cluster._object_namespace, get_id)
        assert loaded.get_dict(True) == cluster.get_dict(True)
        assert hasattr(loaded, '_key'), 'Loaded object is missing _key'

    def test_id_generation(self, provisioner, user):
        provisioner.save(check_status=False)
        user.save()

        empty = Cluster(provisioner._object_namespace, name='test', provisioner=provisioner, owner=user)
        empty.save()

        empty.delete()

    def test_added_key(self, cluster):
        """Test _key is added after saving"""
        cluster_id = cluster.id
        cluster.id = None

        assert not hasattr(cluster, '_key')

        cluster.save()
        assert hasattr(cluster, '_key'), 'Saved object is missing _key'
        cluster.id = cluster_id

    def test_exists(self, cluster):
        assert not Cluster.exists(cluster._object_namespace, cluster.id)

        cluster.save()
        assert Cluster.exists(cluster._object_namespace, cluster.id)

    def test_get_db_key_missing(self, cluster):
        cluster_id = cluster.id
        cluster.id = None

        with pytest.raises(Exception, match=r'Missing object id'):
            cluster.get_db_key()
        cluster.id = cluster_id

    def test_list_with_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list(cluster._object_namespace)
        assert str(cluster.id) in loaded

    def test_list_without_objects(self, cluster):
        cluster.save()

        loaded = Cluster.list(cluster._object_namespace, return_objects=False)
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

        loaded = Cluster.load(cluster._object_namespace, cluster.id)
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


class TestProvisioner:
    @pytest.mark.parametrize('engine', all_engines)
    def test_get_engine_cls(self, provisioner, engine):
        provisioner.engine = 'kqueen.engines.{}'.format(engine)
        provisioner.save(check_status=False)

        engine_class = provisioner.get_engine_cls()

        assert engine_class is not None

    def test_list_engines(self):
        engines = Provisioner.list_engines()

        assert engines == all_engines


class TestProvisionerSerialization:
    def test_load_provisioner(self, user):
        user.save()
        provisioner = Provisioner(
            user.namespace,
            name='Manual provisioner',
            state='OK',
            engine='kqueen.engines.ManualEngine',
            parameters={},
            created_at=datetime.utcnow().replace(microsecond=0),
            owner=user
        )
        provisioner.save()

        loaded = Provisioner.load(user.namespace, provisioner.id)

        assert loaded.get_dict(True) == provisioner.get_dict(True)
        provisioner.delete()


class TestClusterState:
    @pytest.fixture(autouse=True)
    def prepare(self, cluster, monkeypatch):
        def fake_cluster_get(self):
            return {'state': config.get('CLUSTER_PROVISIONING_STATE')}

        monkeypatch.setattr(ManualEngine, 'cluster_get', fake_cluster_get)

        stale_date = datetime.utcnow() - timedelta(days=365)
        cluster.created_at = stale_date
        cluster.save()

        self.cluster = cluster

    def test_stale_cluster(self):
        cluster_state = self.cluster.update_state()
        print(self.cluster.update_state())

        assert cluster_state == config.get('CLUSTER_ERROR_STATE')
