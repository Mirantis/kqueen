from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from kqueen.wrappers import login_required
from kqueen.forms import ProvisionerCreateForm, ClusterCreateForm
from kqueen.tables import ClusterTable, ProvisionerTable

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

user_views = Blueprint('user_views', __name__)


@user_views.route('/')
@login_required
def index():
    username = current_app.config['USERNAME']
    from kqueen.models import Cluster, Provisioner

    clusters = []
    for cluster in list(Cluster.list(return_objects=True).values()):
        data = cluster.get_dict()
        # TODO: teach ORM to get related objects for us
        prv = Provisioner.load(data['provisioner'])
        data['provisioner'] = prv.name.value
        data['actions'] = 'Some Action'
        clusters.append(data)
    clustertable = ClusterTable(clusters)

    provisioners = []
    for provisioner in list(Provisioner.list(return_objects=True).values()):
        data = provisioner.get_dict()
        # TODO: teach get_dict to return properties as well?
        data['engine_name'] = Provisioner.load(data['id']).engine_name
        data['actions'] = 'Some ACtion'
        provisioners.append(data)
    provisionertable = ProvisionerTable(provisioners)

    #clusters = Etcd.cluster.models.all()
    #provisioners = Etcd.provisioner.models.all()

    return render_template('index.html', username=username, clustertable=clustertable, provisionertable=provisionertable)


@user_views.route('/login', methods=['GET', 'POST'])
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


@user_views.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out', 'success')
    return redirect(url_for('user_views.index'))


@user_views.route('/catalog')
@login_required
def catalog():
    return render_template('catalog.html')


@user_views.route('/provisioner-create', methods=['GET', 'POST'])
@login_required
def cluster_deploy():
    form = ProvisionerCreateForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('provisioner_create.html', form=form)


@user_views.route('/cluster-deploy', methods=['GET', 'POST'])
@login_required
def provisioner_create():
    form = ClusterCreateForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('cluster_deploy.html', form=form)


@user_views.route('/cluster-detail')
@login_required
def cluster_detail():
    return render_template('cluster_detail.html')

