from flask import url_for
from io import BytesIO
from kqueen.models import Provisioner

from .forms import _get_provisioners

import pytest


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
