from flask_wtf import FlaskForm
from kqueen.models import Provisioner
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired

PROVISIONER_ENGINES = [('kqueen.engines.JenkinsEngine', 'Jenkins')]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ProvisionerCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    engine = SelectField('Engine', choices=PROVISIONER_ENGINES)
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


def _get_provisioners():
    provisioners = list(Provisioner.list(return_objects=True).values())
    choices = []

    for provisioner in provisioners:
        choices.append((provisioner.id, provisioner.name))

    return choices


class ClusterCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    provisioner = SelectField('Provisioner', choices=_get_provisioners())
