from .helpers import MetricUpdater
from prometheus_client import generate_latest


def test_dummy(user):
    m = MetricUpdater()
    m.update_metrics()

    latest = generate_latest().decode('utf-8')
    print(latest)
