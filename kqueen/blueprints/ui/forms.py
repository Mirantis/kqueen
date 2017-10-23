from flask_wtf import FlaskForm
from kqueen.models import Provisioner
from flask_wtf.file import FileField
from wtforms import PasswordField, SelectField, StringField, TextAreaField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Email

PROVISIONER_ENGINES = [
    ('kqueen.engines.JenkinsEngine', 'Jenkins'),
    ('kqueen.engines.ManualEngine', 'Manual'),
]


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ChangePasswordForm(FlaskForm):
    password_1 = PasswordField('New Password', validators=[DataRequired()])
    password_2 = PasswordField('Repeat Password', validators=[DataRequired()])

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        if not self.password_1.data == self.password_2.data:
            self.password_2.errors.append('Passwords does not match.')
            return False
        return True


class UserCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = EmailField('Email', validators=[Email()])
    password_1 = PasswordField('Password', validators=[DataRequired()])
    password_2 = PasswordField('Repeat Password', validators=[DataRequired()])

    def validate(self):
        if not FlaskForm.validate(self):
            return False
        if not self.password_1.data == self.password_2.data:
            self.password_2.errors.append('Passwords does not match.')
            return False
        return True


class ProvisionerCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    engine = SelectField('Engine', choices=PROVISIONER_ENGINES)
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


def _get_provisioners():
    provisioners = sorted(
        Provisioner.list(return_objects=True).items(),
        key=lambda i: '{}{}'.format(i[1].name, i[1].id)
    )

    choices = []

    for provisioner_name, provisioner in provisioners:
        choices.append((provisioner.id, provisioner.name))

    return choices


class ClusterCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    kubeconfig = FileField()
    provisioner = SelectField('Provisioner', validators=[DataRequired()], choices=[])


class ClusterApplyForm(FlaskForm):
    apply = TextAreaField('Apply Resource', validators=[DataRequired()])
