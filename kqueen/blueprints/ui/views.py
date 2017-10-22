from .forms import _get_provisioners
from .forms import ClusterCreateForm
from .forms import ProvisionerCreateForm
from .forms import ClusterApplyForm
from .forms import ChangePasswordForm
from .forms import UserCreateForm
from .tables import ClusterTable
from .tables import OrganizationMembersTable
from .tables import ProvisionerTable
from .utils import status_for_cluster_detail
from flask import current_app as app
from flask import abort
from flask import Blueprint
from flask import flash
from flask import jsonify
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from kqueen.auth import authenticate
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User
from kqueen.wrappers import login_required
from uuid import UUID

import yaml
import logging
import sys

logger = logging.getLogger(__name__)

ui = Blueprint('ui', __name__, template_folder='templates')


# COntext processor
@ui.context_processor
def inject_username():
    try:
        user = User.load(session['user_id'])
        username = user.username
    except:
        username = ''

    return {'username': username}


# logins
@ui.route('/')
@login_required
def index():
    clusters = []
    healthy_clusters = 0
    for cluster in list(Cluster.list(return_objects=True).values()):
        data = cluster.get_dict()
        if data and 'state' in data:
            if app.config['CLUSTER_ERROR_STATE'] not in data['state']:
                healthy_clusters = healthy_clusters + 1

            # TODO: teach ORM to get related objects for us
            try:
                prv = Provisioner.load(data['provisioner'])
                data['provisioner'] = prv.name
            except:
                pass

            clusters.append(data)

    clustertable = ClusterTable(clusters)
    provisioners = []
    healthy_provisioners = 0
    for provisioner in list(Provisioner.list(return_objects=True).values()):
        data = provisioner.get_dict()
        if data and 'state' in data:
            if app.config['PROVISIONER_ERROR_STATE'] not in data['state']:
                healthy_provisioners = healthy_provisioners + 1

        # TODO: teach get_dict to return properties as well?
        data['engine_name'] = Provisioner.load(data['id']).engine_name
        provisioners.append(data)
    provisionertable = ProvisionerTable(provisioners)

    overview = {
        'cluster_health': int((healthy_clusters / len(clusters)) * 100) if (healthy_clusters and clusters) else 100,
        'provisioner_health': int((healthy_provisioners / len(provisioners)) * 100) if (healthy_provisioners and provisioners) else 100,
    }
    return render_template('ui/index.html', overview=overview, clustertable=clustertable, provisionertable=provisionertable)


@ui.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        user = authenticate(request.form['username'], request.form['password'])
        if user:
            session['user_id'] = user.id
            session['organization_id'] = user.organization
            flash('You were logged in', 'success')
            next_url = request.form.get('next', '')
            if next_url:
                return redirect(next_url)
            return redirect(url_for('.index'))
        else:
            error = 'Invalid credentials'

    return render_template('ui/login.html', error=error)


@ui.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('organization_id', None)
    flash('You were logged out', 'success')
    return redirect(url_for('.index'))


@ui.route('/users/changepw', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            user = User.load(session['user_id'])
            user.password = form.password_1.data
            user.save()
            flash('Password successfully updated. Please log in again.', 'success')
            session.pop('user_id')
            session.pop('organization_id')
            return redirect(url_for('ui.login'))
        except Exception as e:
            logger.error('Could not update password: {}'.format(repr(e)))
            flash('Password update failed.', 'danger')
    return render_template('ui/change_password.html', form=form)


@ui.route('/users/create', methods=['GET', 'POST'])
@login_required
def user_create():
    form = UserCreateForm()
    if form.validate_on_submit():
        try:
            # Instantiate new user DB object
            user = User(
                username=form.username.data,
                password=form.password_1.data,
                email=form.email.data or None,
                organization=session['organization_id']
            )
            user.save()
            flash('User {} successfully created.'.format(user.username), 'success')
        except Exception as e:
            logger.error('Could not create user: {}'.format(repr(e)))
            flash('Could not create user.', 'danger')
        return redirect(url_for('ui.organization_manage'))
    return render_template('ui/user_create.html', form=form)


@ui.route('/users/<user_id>/delete')
@login_required
def user_delete(user_id):
    try:
        object_id = UUID(user_id, version=4)
    except ValueError:
        abort(404)

    # load object
    try:
        obj = User.load(object_id)
        obj.delete()
        flash('User {} successfully deleted.'.format(obj.username), 'success')
        return redirect(request.environ['HTTP_REFERER'])
    except NameError:
        abort(404)
    except Exception as e:
        logger.error(e)
        abort(500)


@ui.route('/organizations/manage')
@login_required
def organization_manage():
    try:
        current_user = User.load(session['user_id'])
        # TODO: teach ORM to get related objects for us
        _org = Organization.load(current_user.organization)
        organization = _org.get_dict()
        users = list(User.list(return_objects=True).values())
        members = [
            u.get_dict()
            for u
            in users
            if u.organization == _org.id and u.id != current_user.id
        ]
        # Patch members until we actually have these data for realsies
        for member in members:
            member['role'] = 'Member'
            member['state'] = 'Active'
            if 'email' not in member:
                member['email'] = '-'
    except:
        organization = {}
        members = []
    membertable = OrganizationMembersTable(members)
    return render_template('ui/organization_manage.html',
                           organization=organization,
                           membertable=membertable)


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
                state=app.config['PROVISIONER_UNKNOWN_STATE'],
                parameters={
                    'username': form.username.data,
                    'password': form.password.data
                }
            )
            provisioner.save()
            flash('Provisioner {} successfully created.'.format(provisioner.name), 'success')
        except Exception as e:
            logger.error('Could not create provisioner: {}'.format(repr(e)))
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
        used_provisioners = [c.provisioner for c in list(Cluster.list(return_objects=True).values())]
        obj = Provisioner.load(object_id)
        if str(object_id) not in used_provisioners:
            obj.delete()
            flash('Provisioner {} successfully deleted.'.format(obj.name), 'success')
        else:
            flash('Provisioner {} is used by deployed cluster, cannot delete.'.format(obj.name), 'warning')
        return redirect('/')
    except NameError:
        abort(404)
    except Exception as e:
        logger.error(e)
        abort(500)


# cluster
@ui.route('/clusters/deploy', methods=['GET', 'POST'])
@login_required
def cluster_deploy():
    form = ClusterCreateForm()
    form.provisioner.choices = _get_provisioners()

    if request.method == 'POST':
        if form.validate_on_submit():
            # Create cluster object
            try:
                # load kubeconfig
                kubeconfig = {}
                kubeconfig_file = form.kubeconfig.data

                if kubeconfig_file:
                    try:
                        kubeconfig = yaml.load(kubeconfig_file.stream)
                    except:
                        logger.error(sys.exc_info())

                cluster = Cluster(
                    name=form.name.data,
                    state=app.config['CLUSTER_PROVISIONING_STATE'],
                    provisioner=form.provisioner.data,
                    kubeconfig=kubeconfig,
                )

                cluster.save()
            except Exception as e:
                flash('Could not create cluster {}.'.format(form.name.data), 'danger')
                logger.error('Creating cluster {} failed with following reason: {}'.format(form.name.data, repr(e)))

                return redirect('/')

            # Actually provision cluster
            result = False

            try:
                result, err = cluster.engine.provision()
            except Exception as e:
                flash('Provisioning failed for {}.'.format(form.name.data), 'danger')
                logger.error('Provisioning cluster {} failed with following reason: {}'.format(form.name.data, repr(e)))
                return redirect('/')

            if result:
                flash('Provisioning of cluster {} is in progress.'.format(form.name.data), 'success')
            else:
                logger.error('Creating cluster {} failed with following reason: {}'.format(form.name.data, str(err)))
                flash('Could not create cluster {}: {}.'.format(form.name.data, err), 'danger')

            return redirect('/')

    return render_template('ui/cluster_deploy.html', form=form)


@ui.route('/clusters/<cluster_id>/detail', methods=['GET', 'POST'])
@login_required
def cluster_detail(cluster_id):
    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        abort(404)

    # load object
    try:
        obj = Cluster.load(object_id)
        obj.get_state()
    except NameError:
        abort(404)

    # load information about clusters
    try:
        cluster_dict = obj.get_dict()
    except:
        cluster_dict = None
        flash('Unable to load cluster', 'danger')

    _status = {}
    state_class = 'info'
    state = obj.get_state()
    if state == app.config['CLUSTER_OK_STATE']:
        state_class = 'success'
        try:
            _status = obj.status()
        except:
            flash('Unable to get information about cluster', 'danger')
    elif state == app.config['CLUSTER_ERROR_STATE']:
        state_class = 'danger'

    status = status_for_cluster_detail(_status)

    form = ClusterApplyForm()
    if form.validate_on_submit():
        obj.apply(form.apply.data)

    return render_template(
        'ui/cluster_detail.html',
        cluster=cluster_dict,
        status=status,
        state_class=state_class,
        form=form
    )


@ui.route('/clusters/<cluster_id>/delete')
@login_required
def cluster_delete(cluster_id):
    # TODO: actually deprovision cluster
    return redirect('/')


@ui.route('/clusters/<cluster_id>/deployment-status')
@login_required
def cluster_deployment_status(cluster_id):
    try:
        object_id = UUID(cluster_id, version=4)
    except ValueError:
        logger.debug('{] not valid UUID'.format(cluster_id))
        abort(404)

    # load object
    try:
        cluster = Cluster.load(object_id)
    except NameError:
        logger.debug('Cluster with UUID {} not found'.format(cluster_id))
        abort(404)

    try:
        status = cluster.engine.get_progress()
    except Exception as e:
        logger.error('Error occured while getting provisioning status for cluster {}: {}'.format(cluster_id, repr(e)))
        abort(500)

    return jsonify(status)
