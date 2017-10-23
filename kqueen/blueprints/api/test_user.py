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
