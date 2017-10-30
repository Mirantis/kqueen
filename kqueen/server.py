from flask import Flask
from flask_jwt import JWT
from kqueen.auth import authenticate, identity
from kqueen.blueprints.api.views import api
from kqueen.serializers import KqueenJSONEncoder
from werkzeug.contrib.cache import SimpleCache
from kqueen.config import current_config

import logging

logger = logging.getLogger(__name__)
cache = SimpleCache()


def create_app(config_file=None):
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = KqueenJSONEncoder

    app.register_blueprint(api, url_prefix='/api/v1')

    # load configuration
    config = current_config()
    logger.info('Loading configuration from {}'.format(config.source_file))
    app.config.from_mapping(config.to_dict())

    return app


app = create_app()
app.logger.setLevel(logging.INFO)
jwt = JWT(app, authenticate, identity)


def run():
    logger.debug('kqueen starting')
    app.run()
