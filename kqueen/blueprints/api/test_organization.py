from .test_crud import BaseTestCRUD
from kqueen.conftest import organization


class TestOrganizationCRUD(BaseTestCRUD):
    def get_object(self):
        return organization()

    def get_edit_data(self):
        return {
            'name': 'patched organization',
            'namespace': 'namespace123',
        }
