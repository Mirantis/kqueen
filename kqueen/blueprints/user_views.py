from flask import Blueprint
from flask import current_app
from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for
from kqueen.wrappers import login_required

import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

user_views = Blueprint('user_views', __name__)


@user_views.route('/')
@login_required
def index():
    return render_template('index.html')


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
