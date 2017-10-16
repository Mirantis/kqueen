from flask_wtf import FlaskForm
from kqueen.models import Provisioner
from flask_wtf.file import FileField
from wtforms import PasswordField, SelectField, StringField
from wtforms.validators import DataRequired

PROVISIONER_ENGINES = [
    ('kqueen.engines.JenkinsEngine', 'Jenkins'),
    ('kqueen.engines.ManualEngine', 'Manual'),
]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ProvisionerCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    engine = SelectField('Engine', choices=PROVISIONER_ENGINES)
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


def _get_provisioners():
    provisioners = Provisioner.list(return_objects=True)
    choices = []

    for provisioner_name, provisioner in sorted(provisioners.items(), key=lambda x: x[1].name):
        choices.append((provisioner.id, provisioner.name))

    return choices


class ClusterCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    provisioner = SelectField('Provisioner', choices=[])
    kubeconfig = FileField()
