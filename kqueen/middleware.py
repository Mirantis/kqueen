from flask import request
from prometheus_client import Counter
from prometheus_client import Histogram

import os
import time

# Prometheus metrics
REQUEST_COUNT = Counter(
    'request_count',
    'HTPP Request Count',
    ['method', 'endpoint', 'http_status']
)
REQUEST_LATENCY = Histogram(
    'request_latency',
    'HTTP Request latency',
    ['method', 'endpoint']
)


def start_timer():
    request.start_time = time.time()


def record_request_data(response):
    resp_time = time.time() - request.start_time

    REQUEST_LATENCY.labels(request.method, request.path).observe(resp_time)
    REQUEST_COUNT.labels(request.method, request.path, response.status_code).inc()

    return response


def setup_metrics(app):
    # TODO: detect multiprocess mode and raise only when needed
    if 'prometheus_multiproc_dir' in os.environ:
        os.makedirs(os.environ['prometheus_multiproc_dir'], exist_ok=True)
    else:
        raise Exception('Please set prometheus_multiproc_dir variable')

    app.before_request(start_timer)
    app.after_request(record_request_data)
