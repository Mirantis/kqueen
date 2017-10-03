from flask_wtf import FlaskForm
from kqueen.models import Provisioner
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


PROVISIONER_ENGINES = [('kqueen.provisioners.jenkins.JenkinsProvisioner', 'JenkinsProvisioner')]

class ProvisionerCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    engine = SelectField('Engine', choices=PROVISIONER_ENGINES)
    access_id = StringField('Access ID', validators=[DataRequired()])
    access_key = PasswordField('Access key', validators=[DataRequired()])


def _get_provisioners():
    prvs = [p.get_dict() for p in list(Provisioner.list(return_objects=True).values())]
    return [(v.get('id', ''), v.get('name', '')) for v in prvs]


class ClusterCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    provisioner = SelectField('Provisioner', choices=_get_provisioners())


