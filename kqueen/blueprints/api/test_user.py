from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import UserFixture
from kqueen.config import current_config

import bcrypt
import json
import pytest


config = current_config()


class TestUserCRUD(BaseTestCRUD):
    def get_object(self):
        return UserFixture()

    def get_edit_data(self):
        return {
            'username': 'patched user',
            'email': 'root@localhost',
        }

    def get_create_data(self):
        data = self.obj.get_dict()
        data['id'] = None
        data['organization'] = 'Organization:{}'.format(self.obj.organization.id)
        data['username'] = 'newusername'

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
        user = self.obj

        assert user.namespace == user.organization.namespace

    def test_password_update(self):
        data = {'password': 'password123'}
        url = url_for('api.user_password_update', pk=self.obj.id)

        response = self.client.patch(
            url,
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        patched = self.obj.__class__.load(
            self.namespace,
            self.obj.id,
        )
        user_password = patched.password.encode('utf-8')
        given_password = "password123".encode('utf-8')
        assert bcrypt.checkpw(given_password, user_password)

    def test_crud_update(self):
        data = self.get_edit_data()

        response = self.client.patch(
            self.urls['update'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        patched = self.obj.__class__.load(
            self.namespace,
            self.obj.id,
        )
        for key, value in data.items():
            assert getattr(patched, key) == value

    @pytest.mark.last
    def test_crud_delete(self):
        super(TestUserCRUD, self).test_crud_delete()
