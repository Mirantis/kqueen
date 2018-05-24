from flask import url_for
from kqueen.conftest import AuthHeader
from kqueen.conftest import UserWithNamespaceFixture
from kqueen.conftest import UserFixture
from kqueen.conftest import etcd_setup
from kqueen.config import current_config

import faker
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

    @pytest.fixture(autouse=True)
    def setup(self, client):
        etcd_setup()
        self.test_object = self.get_object()
        self.obj = self.test_object.obj
        self.obj.save()
        namespace = getattr(self.obj, 'namespace', None) or getattr(getattr(self.obj, 'owner', None), 'namespace', None)
        self.test_user = UserFixture(namespace)
        self.test_auth_header = AuthHeader(self.test_user)
        self.auth_header = self.test_auth_header.get(client)
        self.namespace = self.auth_header['X-Test-Namespace']

        self.urls = self.get_urls()

    def teardown(self):
        self.test_auth_header.destroy()
        self.test_object.destroy()

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
            headers=self.auth_header
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
            headers=self.auth_header
        )

        assert response.status_code == 200
        with pytest.raises(NameError, message='Object not found'):
            self.obj.__class__.load(
                self.namespace,
                self.obj.id,
            )

    def test_crud_delete_failed(self, monkeypatch):
        original_delete = getattr(self.obj.__class__, 'delete')

        def fake_delete(self, *args, **kwargs):
            raise Exception('Testing')

        monkeypatch.setattr(self.obj.__class__, 'delete', fake_delete)

        response = self.client.delete(self.urls['delete'], headers=self.auth_header)

        assert response.status_code == 500
        monkeypatch.setattr(self.obj.__class__, 'delete', original_delete)

    #
    # namespacing tests
    #

    def test_namespacing(self):
        user1 = UserWithNamespaceFixture()
        user1.auth_header = AuthHeader(user1).get(self.client)
        user2 = UserWithNamespaceFixture()
        user2.auth_header = AuthHeader(user2).get(self.client)

        # skip if object class isn't namespaced
        if not self.obj.__class__.is_namespaced():
            pytest.skip('Class {} isn\'t namespaced'.format(self.obj.__class__.__name__))

        objs = {}

        # create objects for both users
        for u in [user1, user2]:
            data = self.get_create_data()

            organization_ref = 'Organization:{}'.format(u.obj.organization.id)
            profile = faker.Faker().simple_profile()
            owner_data = {
                'username': profile['username'],
                'email': profile['mail'],
                'password': 'pytest',
                'organization': organization_ref,
                'role': 'admin',
                'active': True
            }
            response = self.client.post(
                url_for('api.user_create'),
                data=json.dumps(owner_data),
                headers=u.auth_header,
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
                    headers=u.auth_header,
                    content_type='application/json',
                )
                data['provisioner'] = 'Provisioner:{}'.format(response.json['id'])

            response = self.client.post(
                self.urls['create'],
                data=json.dumps(data),
                headers=u.auth_header,
                content_type='application/json',
            )

            print(response.data.decode(response.charset))
            objs[u.obj.namespace] = response.json['id']

            print(response.json)

        # test use can't read other's object
        for u in [user1, user2]:

            for ns, pk in objs.items():
                url = self.get_urls(pk)['get']

                if ns == u.obj.namespace:
                    req_code = 200
                else:
                    req_code = 404

                response = self.client.get(
                    url,
                    headers=u.auth_header,
                    content_type='application/json',
                )

                print(response.data.decode(response.charset))
                assert response.status_code == req_code
