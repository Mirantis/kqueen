from flask import Blueprint
from flask import current_app
from flask import make_response
from flask import request
from flask_jwt import _jwt_required
from ipaddress import ip_address
from ipaddress import ip_network
from prometheus_client import CollectorRegistry
from prometheus_client import CONTENT_TYPE_LATEST
from prometheus_client import generate_latest
from prometheus_client import multiprocess

metrics = Blueprint('metrics', __name__)


@metrics.route('/')
def root():
    # check access
    ip_whitelist = ip_network(current_app.config.get('PROMETHEUS_WHITELIST'))
    if ip_address(request.remote_addr) not in ip_whitelist:
        _jwt_required(current_app.config['JWT_DEFAULT_REALM'])

    registry = CollectorRegistry()
    multiprocess.MultiProcessCollector(registry)

    data = generate_latest(registry)

    response = make_response(data)
    response.headers['Content-Type'] = CONTENT_TYPE_LATEST
    response.headers['Content-Length'] = str(len(data))

    return response
