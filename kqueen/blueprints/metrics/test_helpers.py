from .helpers import MetricUpdater
from prometheus_client import generate_latest

import pytest


class TestMetricUpdates:
    @pytest.fixture(scope='class')
    def latest(self, user):
        user.save()

        m = MetricUpdater()
        m.update_metrics()

        return generate_latest().decode('utf-8')

    @pytest.mark.parametrize('metric', [
        ('users_by_namespace{namespace="demoorg"}'),
        ('users_by_role{role="superadmin"}'),
        ('users_active'),
        ('organization_count'),
    ])
    def test_metrics_exist(user, latest, metric):

        req = "{metric} ".format(metric=metric)

        assert req in latest
