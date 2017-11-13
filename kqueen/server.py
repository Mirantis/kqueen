from flask import Flask
from flask_jwt import JWT
from flask_swagger_ui import get_swaggerui_blueprint
from kqueen.auth import authenticate, identity
from kqueen.blueprints.api.views import api
from kqueen.serializers import KqueenJSONEncoder
from werkzeug.contrib.cache import SimpleCache
from kqueen.config import current_config
from .storages.etcd import EtcdBackend

import logging

logger = logging.getLogger(__name__)
cache = SimpleCache()
swagger_url = '/api/docs'
api_url = '/api/v1/swagger'

swaggerui_blueprint = get_swaggerui_blueprint(
    swagger_url,
    api_url,
    config={
        'docExpansion': 'none'
    }
)


def create_app(config_file=None):
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = KqueenJSONEncoder

    app.register_blueprint(api, url_prefix='/api/v1')
    app.register_blueprint(swaggerui_blueprint, url_prefix=swagger_url)

    # load configuration
    config = current_config(config_file)
    app.config.from_mapping(config.to_dict())
    app.logger.setLevel(getattr(logging, app.config.get('LOG_LEVEL')))
    app.logger.info('Loading configuration from {}'.format(config.source_file))

    # setup database
    app.db = EtcdBackend()

    # setup JWT
    JWT(app, authenticate, identity)

    return app


app = create_app()


def run():
    logger.debug('kqueen starting')
    app.run(host=app.config.get('KQUEEN_HOST', '127.0.0.1'),
            port=int(app.config.get('KQUEEN_PORT', 5000)))
