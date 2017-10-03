from .forms import ClusterCreateForm
from .forms import ProvisionerCreateForm
from .tables import ClusterTable
from .tables import ProvisionerTable
from flask import abort
from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from kqueen.models import Cluster
from kqueen.models import Provisioner
from kqueen.wrappers import login_required
from uuid import UUID

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ui = Blueprint('ui', __name__, template_folder='templates')


# logins
@ui.route('/')
@login_required
def index():
    username = current_app.config['USERNAME']

    clusters = []
    for cluster in list(Cluster.list(return_objects=True).values()):
        data = cluster.get_dict()
        # TODO: teach ORM to get related objects for us
        try:
            prv = Provisioner.load(data['provisioner'])
            data['provisioner'] = prv.name.value
        except:
            pass
        clusters.append(data)
    clustertable = ClusterTable(clusters)

    provisioners = []
    for provisioner in list(Provisioner.list(return_objects=True).values()):
        data = provisioner.get_dict()
        # TODO: teach get_dict to return properties as well?
        data['engine_name'] = Provisioner.load(data['id']).engine_name
        provisioners.append(data)
    provisionertable = ProvisionerTable(provisioners)

    return render_template('ui/index.html', username=username, clustertable=clustertable, provisionertable=provisionertable)


@ui.route('/login', methods=['GET', 'POST'])
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

    return render_template('ui/login.html', error=error)


@ui.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('You were logged out', 'success')
    return redirect(url_for('ui.index'))


# catalog
@ui.route('/catalog')
@login_required
def catalog():
    return render_template('ui/catalog.html')


# provisioner
@ui.route('/provisioners/create', methods=['GET', 'POST'])
@login_required
def provisioner_create():
    form = ProvisionerCreateForm()
    if form.validate_on_submit():
        try:
            # Instantiate new provisioner DB object
            provisioner = Provisioner(
                name=form.name.data,
                engine=form.engine.data,
                state='Not Available',
                location='-',
                access_id=form.access_id.data,
                access_key=form.access_key
            )
            # Check if provisioner lives
            if provisioner.alive():
                provisioner.state.value = 'OK'
            provisioner.save()
            flash('Provisioner %s successfully created.' % provisioner.name, 'success')
        except Exception as e:
            logging.error('Could not create provisioner: %s' % repr(e))
            flash('Could not create provisioner.', 'danger')
        return redirect('/')
    return render_template('ui/provisioner_create.html', form=form)


@ui.route('/provisioners/<provisioner_id>/delete')
@login_required
def provisioner_delete(provisioner_id):
    try:
        object_id = UUID(provisioner_id, version=4)
    except ValueError:
        abort(404)

    # load object
    try:
        used_provisioners = [c.provisioner.value for c in list(Cluster.list(return_objects=True).values())]
        obj = Provisioner.load(object_id)
        if str(object_id) not in used_provisioners:
            obj.delete()
            flash('Provisioner %s successfully deleted.' % obj.name, 'success')
        else:
            flash('Provisioner %s is used by deployed cluster, cannot delete.' % obj.name, 'warning')
        return redirect('/')
    except NameError:
        abort(404)
    except Exception as e:
        logging.error(e)
        abort(500)


# cluster
@ui.route('/clusters/deploy', methods=['GET', 'POST'])
@login_required
def cluster_deploy():
    form = ClusterCreateForm()
    if form.validate_on_submit():
        return redirect('/')
    return render_template('ui/cluster_deploy.html', form=form)


@ui.route('/clusters/<cluster_id>/detail')
@login_required
def cluster_detail(cluster_id):
    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(404)

    # load object
    try:
        obj = Cluster.load(object_id)
    except NameError:
        abort(404)

    return render_template(
        'ui/cluster_detail.html',
        cluster=obj.get_dict(),
        status=obj.status(),
    )


@ui.route('/clusters/<cluster_id>/delete')
@login_required
def cluster_delete(cluster_id):
    # TODO: actually deprovision cluster
    return redirect('/')

