from flask import url_for
from kqueen.conftest import AuthHeader
from kqueen.models import User
from datetime import datetime

import json
import pytest
import yaml


@pytest.mark.usefixtures('client_class')
class TestInsertManualCluster:
    def setup(self):
        self.auth_header_test = AuthHeader()
        self.auth_header = self.auth_header_test.get(self.client)
        self.namespace = self.auth_header['X-Test-Namespace']
        self.user = User.load(None, self.auth_header['X-User'])

        self.provisioner_id = None

    def teardown(self):
        self.auth_header_test.destroy()

    def test_run(self):
        self.create_provisioner()
        self.get_provisioners()
        self.create_cluster()
        self.get_cluster()

    def create_provisioner(self):
        data = {
            'name': 'Manual provisioner',
            'engine': 'kqueen.engines.ManualEngine',
            'owner': 'User:{}'.format(self.user.id),
        }

        response = self.client.post(
            url_for('api.provisioner_create'),
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200

        self.provisioner_id = response.json['id']

    def get_provisioners(self):
        response = self.client.get(
            url_for('api.provisioner_list'),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200

        content = response.data.decode(response.charset)
        assert self.provisioner_id in content

    def create_cluster(self):
        data = {
            'name': 'Manual cluster',
            'provisioner': 'Provisioner:{}'.format(self.provisioner_id),
            'kubeconfig': yaml.load(open('kubeconfig_localhost', 'r').read()),
            'owner': 'User:{}'.format(self.user.id),
            'created_at': str(datetime.utcnow()),
        }

        response = self.client.post(
            url_for('api.cluster_create'),
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        self.cluster_id = response.json['id']

    def get_cluster(self):
        response = self.client.get(
            url_for('api.cluster_get', pk=self.cluster_id),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
