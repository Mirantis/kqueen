from .helpers import MetricUpdater
from prometheus_client import generate_latest

import pytest


class TestMetricUpdates:
    @pytest.fixture(scope='class')
    def latest(self):
        m = MetricUpdater()
        m.update_metrics()

        return generate_latest().decode('utf-8')

    @pytest.mark.parametrize('metric, value', [
        ('users_by_namespace{namespace="demoorg"}', 1.0),
        ('users_by_role{role="superadmin"}', 1.0),
        ('users_active', 1.0),
        ('organization_count', 1.0),
    ])
    def test_metrics_exist(user, latest, metric, value):

        req = "{metric} {value}".format(metric=metric, value=value)

        assert req in latest
