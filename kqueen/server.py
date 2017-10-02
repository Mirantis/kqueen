from flask import Flask
from kqueen.blueprints.api import api
from kqueen.blueprints.user_views import user_views
from kqueen.serializers import CustomJSONEncoder

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = CustomJSONEncoder

    app.register_blueprint(user_views)
    app.register_blueprint(api, url_prefix='/api/v1')

    # DEMO LOGIN
    app.config.update(dict(
        USERNAME='admin',
        PASSWORD='default',
        SECRET_KEY='secret'
    ))

    return app


def run():
    logger.debug('kqueen starting')

    app = create_app()
    app.run(debug=True)
