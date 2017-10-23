from flask import url_for
from uuid import uuid4

import pytest


class TestProvisionerList:
    def test_provisioner_list(self, provisioner, client, auth_header):
        provisioner.save()

        response = client.get(url_for('api.provisioner_list'), headers=auth_header)
        assert provisioner.get_dict() in response.json


class TestProvisionerDetails:
    def test_provisioner_detail(self, provisioner, client, auth_header):
        provisioner.save()
        provisioner_id = provisioner.id

        response = client.get(url_for('api.provisioner_detail', provisioner_id=provisioner_id), headers=auth_header)
        assert response.json == provisioner.get_dict()

    @pytest.mark.parametrize('provisioner_id,status_code', [
        (uuid4(), 404),
        ('wrong-uuid', 400),
    ])
    def test_object_not_found(self, client, provisioner_id, auth_header, status_code):
        response = client.get(url_for('api.provisioner_detail', provisioner_id=provisioner_id), headers=auth_header)
        assert response.status_code == status_code
