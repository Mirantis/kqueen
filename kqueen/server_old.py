from flask import abort
from flask import Flask
from flask import jsonify
from flask import make_response
from kqueen.provisioners.jenkins import JenkinsProvisioner

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

provisioner = JenkinsProvisioner()


@app.route('/')
def index():
    return "Gutten tag"


# error handlers
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(501)
def not_implemented(error):
    return make_response(jsonify({'error': 'Not implemented'}), 501)


# clusters
@app.route('/api/v1/clusters', methods=['GET'])
def list_clusters():
    clusters = provisioner.list()
    return jsonify({'clusters': clusters})


@app.route('/api/v1/clusters/<int:cluster_id>', methods=['GET'])
def detail_cluster(cluster_id):
    abort(501)


@app.route('/api/v1/clusters', methods=['POST'])
def create_cluster():
    abort(501)


def run():
    logger.debug('kqueen starting')
    app.run(debug=True)
