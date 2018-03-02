from .__init__ import __all__ as all_engines
from .base import BaseEngine
from .jenkins import JenkinsEngine

import pytest

required_methods = [
    'cluster_list',
    'cluster_get',
    'provision',
    'get_kubeconfig',
    'get_progress',
]

engines = [
    JenkinsEngine,
]


class TestBaseEngine:
    @pytest.mark.parametrize('attr_name', ['name', 'verbose_name'])
    def test_class_attrs(self, cluster, attr_name):
        engine = BaseEngine(cluster)

        assert hasattr(engine.__class__, attr_name)

    @pytest.mark.parametrize('attr_name', required_methods)
    def test_object_attrs(self, cluster, attr_name):
        engine = BaseEngine(cluster)
        attr = getattr(engine, attr_name)

        with pytest.raises(NotImplementedError):
            attr()

    def test_engine_status(self, cluster, app, **kwargs):
        engine = BaseEngine(cluster)
        assert engine.engine_status(**kwargs) == app.config.get('PROVISIONER_OK_STATE')

    def test_get_parameter_schema(self, cluster):
        engine = BaseEngine(cluster)
        assert engine.get_parameter_schema() == engine.parameter_schema

    def test_deprovision(self, cluster):
        engine = BaseEngine(cluster)
        result, error = engine.deprovision()
        assert result is False


class TestAllEngines:
    @pytest.mark.parametrize('engine_class', engines)
    def test_engines_equal_all(self, engine_class):
        assert engine_class.__name__ in all_engines

    @pytest.mark.parametrize('method_name', required_methods)
    @pytest.mark.parametrize('engine_class', engines)
    def test_engine_implements_required_methods(self, engine_class, method_name, cluster):
        engine = engine_class(cluster)

        assert hasattr(engine, method_name)

        method = getattr(engine, method_name)
        try:
            method()
        except NotImplementedError:
            pytest.fail('Engine {} missing method {}'.format(engine_class.__name__, method_name))
        except Exception:
            pass
