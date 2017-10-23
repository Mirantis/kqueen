from flask import url_for
from kqueen.conftest import auth_header

import json
import pytest


@pytest.mark.usefixtures('client_class')
class BaseTestCRUD:
    def get_object(self):
        raise NotImplementedError

    def get_resource_type(self):
        return self.obj.__class__.__name__.lower()

    def get_edit_data(self):
        raise NotImplementedError

    def get_urls(self):

        return {
            'list': url_for(
                'api.{}_list'.format(self.get_resource_type())
            ),
            'create': url_for(
                'api.{}_create'.format(self.get_resource_type())
            ),
            'get': url_for(
                'api.{}_get'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
            'update': url_for(
                'api.{}_update'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
            'delete': url_for(
                'api.{}_delete'.format(self.get_resource_type()),
                pk=self.obj.id
            ),
        }

    def setup(self):
        self.obj = self.get_object()
        self.obj.save()

        self.auth_header = auth_header(self.client)
        self.urls = self.get_urls()

    def test_crud_create(self):
        data = self.obj.get_dict()
        data['id'] = None

        response = self.client.post(
            self.urls['create'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200

        response_dict = json.loads(response.json)
        assert response_dict['id'] != self.obj.id

    def test_crud_create_not_json(self):
        response = self.client.post(
            self.urls['create'],
            headers=self.auth_header,
            content_type='text/plain',
        )

        assert response.status_code == 400

    def test_crud_create_failed_save(self, monkeypatch):
        def fake_save(self, *args, **kwargs):
            raise Exception('Test')

        monkeypatch.setattr(self.obj.__class__, 'save', fake_save)
        data = self.obj.get_dict()
        data['id'] = None

        response = self.client.post(
            self.urls['create'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 500

    def test_crud_get(self):
        response = self.client.get(
            self.urls['get'],
            headers=self.auth_header,
        )

        assert response.status_code == 200
        assert response.json == self.obj.get_dict()

    def test_crud_list(self):
        response = self.client.get(
            self.urls['list'],
            headers=self.auth_header,
        )

        data = response.json

        assert isinstance(data, list)
        assert len(data) == len(self.obj.__class__.list(return_objects=False))
        assert self.obj.get_dict() in data

    def test_crud_update(self):
        data = self.get_edit_data()

        response = self.client.patch(
            self.urls['update'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        patched = self.obj.__class__.load(self.obj.id)
        for key, value in data.items():
            assert getattr(patched, key) == value

    @pytest.mark.parametrize('data,content_type,code', [
        ('hello', 'text/plain', 400),
        ('[1, 2, 3]', 'application/json', 400),
    ])
    def test_crud_update_return_error(self, data, content_type, code):
        response = self.client.patch(
            self.urls['update'],
            data=data,
            headers=self.auth_header,
            content_type=content_type,
        )

        assert response.status_code == code

    def test_crud_update_failed_save(self, monkeypatch):
        def fake_save(self, *args, **kwargs):
            raise Exception('Testing')

        monkeypatch.setattr(self.obj.__class__, 'save', fake_save)

        data = self.get_edit_data()
        response = self.client.patch(
            self.urls['update'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 500

    def test_crud_delete(self):
        response = self.client.delete(
            self.urls['delete'],
            headers=self.auth_header,
        )

        assert response.status_code == 200
        with pytest.raises(NameError, message='Object not found'):
            self.obj.__class__.load(self.obj.id)

    def test_crud_delete_failed(self, monkeypatch):
        def fake_delete(self, *args, **kwargs):
            raise Exception('Testing')

        monkeypatch.setattr(self.obj.__class__, 'delete', fake_delete)

        response = self.client.delete(
            self.urls['delete'],
            headers=self.auth_header,
        )

        assert response.status_code == 500
