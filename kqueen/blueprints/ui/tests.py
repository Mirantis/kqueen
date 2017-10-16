from flask import url_for
from kqueen.models import Provisioner
from .forms import _get_provisioners
from io import BytesIO

import pytest


@pytest.mark.parametrize('view,values', [
    ('ui.index', {}),
    ('ui.catalog', {}),
    ('ui.provisioner_create', {'provisioner_id': 1}),
    ('ui.provisioner_delete', {'provisioner_id': 1}),
    ('ui.cluster_detail', {'cluster_id': 1}),
])
def test_login_required(client, view, values):
    response = client.get(url_for(view, **values))

    assert response.status_code == 302


def test_index(client_login):
    response = client_login.get(url_for('.index'))
    assert response.status_code == 200


def test_logout(client_login):
    response = client_login.get(url_for('.logout'))
    assert response.status_code == 302
    assert response.headers['Location'].endswith(url_for('.index'))


class TestProvisionerForm:
    def test_get_provisioners(self):
        provisioners = sorted(
            Provisioner.list(return_objects=True).items(),
            key=lambda i: '{}{}'.format(i[1].name, i[1].id)
        )

        choices = []

        # create list of choices
        for provisioner_name, provisioner in provisioners:
            choices.append((provisioner.id, provisioner.name))

        assert _get_provisioners() == choices


class TestKubeconfigUpload:
    def setup(self):
        # create file
        self.fd = BytesIO(b'binary file')
        self.fd.name = 'kubeconfig.yml'

    @pytest.mark.skip('Not implemented yet')
    def test_upload_kubeconfig(self, client_login, provisioner, cluster):
        provisioner.save()
        cluster.name = 'test_cluster'

        url = url_for('ui.cluster_deploy')
        print(url)

        response = client_login.post(url, data={
            'name': cluster.name,
            'provisioner': provisioner.id,
            'kubeconfig': self.fd,
        })

        content = response.data.decode(response.charset)

        assert response.status_code == 200
        assert 'Provisioning of cluster {} is in progress'.format(cluster.name) in content
