from flask import Flask
from flask import redirect
from flask import url_for
from flask_jwt import JWT
from kqueen.auth import authenticate, identity
from kqueen.blueprints.api.views import api
from kqueen.serializers import KqueenJSONEncoder
from werkzeug.contrib.cache import SimpleCache

import logging
import os

logger = logging.getLogger(__name__)

cache = SimpleCache()

config_file = os.environ.get('KQUEEN_CONFIG_FILE', 'config/dev.py')


def create_app(config_file=config_file):
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = KqueenJSONEncoder

    app.register_blueprint(api, url_prefix='/api/v1')

    # load configuration
    if app.config.from_pyfile(config_file):
        logger.info('Loading configuration from {}'.format(config_file))
    else:
        raise Exception('Config file {} could not be loaded.'.format(config_file))

    return app


app = create_app()
app.logger.setLevel(logging.INFO)
jwt = JWT(app, authenticate, identity)


def run():
    logger.debug('kqueen starting')
    app.run()
