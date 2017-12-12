from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import user
from kqueen.config import current_config

import json
import pytest

config = current_config()


class TestUserCRUD(BaseTestCRUD):
    def get_object(self):
        return user()

    def get_edit_data(self):
        return {
            'username': 'patched user',
            'email': 'root@localhost',
            'password': 'password123',
        }

    def get_create_data(self):
        data = self.obj.get_dict()
        data['id'] = None
        data['organization'] = 'Organization:{}'.format(self.obj.organization.id)

        return data

    def get_auth_headers(self):
        """
        Get auth token for user in self.obj

        Returns:
            dict: Authorization header dict
        """
        data = {'username': self.obj.username, 'password': self.obj.username + 'password'}

        response = self.client.post(
            '/api/v1/auth',
            data=json.dumps(data),
            content_type='application/json')

        return {'Authorization': '{header_prefix} {token}'.format(
            header_prefix=config.get('JWT_AUTH_HEADER_PREFIX'),
            token=response.json['access_token'],
        )}

    def test_whoami(self):
        url = url_for('api.user_whoami')

        response = self.client.get(
            url,
            headers=self.get_auth_headers(),
            content_type='application/json',
        )

        assert response.json == self.obj.get_dict(expand=True)

    def test_namespace(self):
        user = self.get_object()

        assert user.namespace == user.organization.namespace

    @pytest.mark.last
    def test_crud_delete(self):
        super(TestUserCRUD, self).test_crud_delete()
