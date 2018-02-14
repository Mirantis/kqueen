from .auth import authenticate
from .auth import identity
from .blueprints.api.views import api
from .blueprints.metrics.views import metrics
from .config import current_config
from .exceptions import ImproperlyConfigured
from .middleware import setup_metrics
from .serializers import KqueenJSONEncoder
from .storages.etcd import EtcdBackend
from flask import Flask
from flask_jwt import JWT
from flask_swagger_ui import get_swaggerui_blueprint
from kqueen.utils.loggers import setup_logging
from werkzeug.contrib.cache import SimpleCache

import logging

# Logging configuration
config = current_config(config_file=None)
setup_logging(config.get('LOG_CONFIG'), config.get('LOG_LEVEL'))
logger = logging.getLogger('kqueen_api')

cache = SimpleCache()
swagger_url = '/api/docs'
api_url = '/api/v1/swagger'

swaggerui_blueprint = get_swaggerui_blueprint(
    swagger_url,
    api_url,
    config={
        'docExpansion': 'list'
    }
)


def create_app(config_file=None):
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = KqueenJSONEncoder

    app.register_blueprint(api, url_prefix='/api/v1')
    app.register_blueprint(metrics, url_prefix='/metrics')
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)

    # load configuration
    config = current_config(config_file)
    config.setup_policies()

    secret_key = config.get('SECRET_KEY')
    if not secret_key or len(secret_key) < 16:
        raise ImproperlyConfigured('The SECRET_KEY must be set and longer than 16 chars.')

    app.config.from_mapping(config.to_dict())
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL')))
    app.logger.info('Loading configuration from {}'.format(config.source_file))

    # setup database
    app.db = EtcdBackend()

    # setup JWT
    JWT(app, authenticate, identity)

    # setup metrics
    setup_metrics(app)

    return app


app = create_app()


def run():
    logger.debug('kqueen starting')
    app.run(
        host=app.config.get('KQUEEN_HOST'),
        port=int(app.config.get('KQUEEN_PORT'))
    )
