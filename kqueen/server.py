from flask import Flask
from flask import redirect
from flask import url_for
from kqueen.blueprints.api.views import api
from kqueen.blueprints.ui.views import ui
from kqueen.serializers import CustomJSONEncoder
from werkzeug.contrib.cache import SimpleCache

import logging
import os

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cache = SimpleCache()

config_file = os.environ.get('KQUEEN_CONFIG_FILE', 'config/dev.py')


def create_app(config_file=config_file):
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = CustomJSONEncoder

    app.register_blueprint(ui, url_prefix='/ui')
    app.register_blueprint(api, url_prefix='/api/v1')

    # load configuration
    if app.config.from_pyfile(config_file):
        logger.info('Loading configuration from {}'.format(config_file))
    else:
        raise Exception('Config file {} could not be loaded.'.format(config_file))

    return app


application = create_app()


@application.route('/')
def root():
    return redirect(url_for('ui.index'), code=302)


def run():
    logger.debug('kqueen starting')
    application.run()
