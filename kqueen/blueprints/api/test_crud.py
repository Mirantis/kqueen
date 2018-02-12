from flask import url_for
from kqueen.conftest import auth_header, user_with_namespace, get_auth_token
from kqueen.config import current_config

import json
import pytest

config = current_config()


@pytest.mark.usefixtures('client_class')
class BaseTestCRUD:
    def get_object(self):
        raise NotImplementedError

    def get_edit_data(self):
        raise NotImplementedError

    def get_resource_type(self):
        return self.obj.__class__.__name__.lower()

    def get_create_data(self):
        data = self.obj.get_dict(expand=True)
        data['id'] = None

        return data

    def get_urls(self, pk=None):

        if not pk:
            pk = self.obj.id

        return {
            'list': url_for(
                'api.{}_list'.format(self.get_resource_type())
            ),
            'create': url_for(
                'api.{}_create'.format(self.get_resource_type())
            ),
            'get': url_for(
                'api.{}_get'.format(self.get_resource_type()),
                pk=pk
            ),
            'update': url_for(
                'api.{}_update'.format(self.get_resource_type()),
                pk=pk
            ),
            'delete': url_for(
                'api.{}_delete'.format(self.get_resource_type()),
                pk=pk
            ),
        }

    def setup(self):
        self.obj = self.get_object()
        self.obj.save()

        self.auth_header = auth_header(self.client)
        self.namespace = self.auth_header['X-Test-Namespace']
        self.urls = self.get_urls()

    def test_crud_create(self):
        data = self.get_create_data()

        response = self.client.post(
            self.urls['create'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json['id'] != self.obj.id

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
        data = self.get_create_data()

        response = self.client.post(
            self.urls['create'],
            data=json.dumps(data),
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 500

    def test_crud_get(self):
        self.obj.save()

        response = self.client.get(
            self.urls['get'],
            headers=self.auth_header,
        )

        # object might have been updated during GET
        obj = self.obj.__class__.load(
            self.namespace,
            self.obj.id
        )

        assert response.status_code == 200
        assert response.json == obj.get_dict(expand=True)

    def test_crud_list(self):
        response = self.client.get(
            self.urls['list'],
            headers=self.auth_header,
        )

        data = response.json

        # object might have been updated during LIST
        obj = self.obj.__class__.load(
            self.namespace,
            self.obj.id
        )

        assert isinstance(data, list)
        assert len(data) == len(self.obj.__class__.list(
            self.namespace,
            return_objects=False)
        )
        assert obj.get_dict(expand=True) in data

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
            self.obj.__class__.load(
                self.namespace,
                self.obj.id,
            )

    def test_crud_delete_failed(self, monkeypatch):
        def fake_delete(self, *args, **kwargs):
            raise Exception('Testing')

        monkeypatch.setattr(self.obj.__class__, 'delete', fake_delete)

        response = self.client.delete(
            self.urls['delete'],
            headers=self.auth_header,
        )

        assert response.status_code == 500

    #
    # namespacing tests
    #
    @pytest.fixture
    def setup_namespace(self):
        self.user1 = user_with_namespace()
        self.user2 = user_with_namespace()

    @pytest.mark.usefixtures('setup_namespace')
    def test_namespacing(self, client):
        obj = self.get_object()

        # skip if object class isn't namespaced
        if not obj.__class__.is_namespaced():
            pytest.skip('Class {} isn\'t namespaced'.format(obj.__class__.__name__))

        objs = {}

        # create objects for both users
        for u in [self.user1, self.user2]:
            data = self.get_create_data()

            auth_header = get_auth_token(self.client, u)
            headers = {
                'Authorization': '{} {}'.format(
                    config.get('JWT_AUTH_HEADER_PREFIX'),
                    auth_header
                )
            }

            # TODO: fix this
            # Dirty hack to make testing data namespaced.
            organization_data = {
                'name': 'Test organization',
                'namespace': 'testorg',
            }
            response = self.client.post(
                url_for('api.organization_create'),
                data=json.dumps(organization_data),
                headers=headers,
                content_type='application/json',
            )
            organization_ref = 'Organization:{}'.format(response.json['id'])
            owner_data = {
                'username': 'Test owner',
                'email': 'owner@pytest.org',
                'password': 'pytest',
                'organization': organization_ref,
                'role': 'admin',
                'active': True
            }
            response = self.client.post(
                url_for('api.user_create'),
                data=json.dumps(owner_data),
                headers=headers,
                content_type='application/json',
            )
            if 'owner' in data:
                data['owner'] = 'User:{}'.format(response.json['id'])
            if 'provisioner' in data:
                provisioner_data = {
                    'name': 'Test provisioner',
                    'engine': 'kqueen.engines.ManualEngine',
                    'owner': 'User:{}'.format(response.json['id'])
                }
                response = self.client.post(
                    url_for('api.provisioner_create'),
                    data=json.dumps(provisioner_data),
                    headers=headers,
                    content_type='application/json',
                )
                data['provisioner'] = 'Provisioner:{}'.format(response.json['id'])

            response = self.client.post(
                self.urls['create'],
                data=json.dumps(data),
                headers=headers,
                content_type='application/json',
            )

            print(response.data.decode(response.charset))
            objs[u.namespace] = response.json['id']

            print(response.json)

        # test use can't read other's object
        for u in [self.user1, self.user2]:
            auth_header = get_auth_token(self.client, u)
            headers = {
                'Authorization': '{} {}'.format(
                    config.get('JWT_AUTH_HEADER_PREFIX'),
                    auth_header
                )
            }

            for ns, pk in objs.items():
                url = self.get_urls(pk)['get']

                if ns == u.namespace:
                    req_code = 200
                else:
                    req_code = 404

                response = self.client.get(
                    url,
                    headers=headers,
                    content_type='application/json',
                )

                print(response.data.decode(response.charset))
                assert response.status_code == req_code
