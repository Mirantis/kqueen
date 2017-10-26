from .test_crud import BaseTestCRUD
from kqueen.conftest import user


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
