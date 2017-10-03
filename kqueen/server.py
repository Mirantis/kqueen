from flask import Flask
from flask import redirect
from flask import url_for
from kqueen.blueprints.api.views import api
from kqueen.blueprints.ui.views import ui
from kqueen.serializers import CustomJSONEncoder

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def create_app():
    app = Flask(__name__, static_folder='./asset/static')
    app.json_encoder = CustomJSONEncoder

    app.register_blueprint(ui, url_prefix='/ui')
    app.register_blueprint(api, url_prefix='/api/v1')
    loaded = app.config.from_pyfile('config.py', silent=True)
    if not loaded:
        logging.warning('Config file kqueen.cfg could not be loaded.')
    return app


def run():
    logger.debug('kqueen starting')
    app = create_app()

    @app.route('/')
    def root():
        return redirect(url_for('ui.index'), code=302)

    # TODO: make debug code optional
    app.run(debug=True)
