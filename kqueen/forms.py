from flask_wtf import Form
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired


class LoginForm(Form):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class ProvisionerCreateForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    access_id = StringField('Access ID', validators=[DataRequired()])
    access_key = StringField('Access key', validators=[DataRequired()])


class ClusterCreateForm(Form):
    name = StringField('Name', validators=[DataRequired()])
    provisioner = StringField('Provisioner', validators=[DataRequired()])
