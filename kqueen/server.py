from flask import abort
from flask import current_app
from flask import flash
from flask import Flask
from flask import jsonify
from flask import make_response
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from functools import wraps
from kqueen.provisioners.jenkins import JenkinsProvisioner

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
app = Flask(__name__, static_folder='./asset/static')

# DEMO LOGIN
app.config.update(dict(
    USERNAME='admin',
    PASSWORD='default',
    SECRET_KEY='secret'
))

provisioner = JenkinsProvisioner()


############
# WRAPPERS #
############

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in', False):
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


##############
# USER VIEWS #
##############

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != current_app.config['USERNAME']:
            error = 'Invalid username'
        elif request.form['password'] != current_app.config['PASSWORD']:
            error = 'Invalid password'
        else:
            session['logged_in'] = True
            flash('You were logged in', 'success')
            next_url = request.form.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('index'))

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out', 'success')

    return redirect(url_for('index'))


##############
# JSON VIEWS #
##############

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
