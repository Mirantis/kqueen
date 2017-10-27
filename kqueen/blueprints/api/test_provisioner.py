from .test_crud import BaseTestCRUD
from kqueen.conftest import provisioner


class TestProvisionerCRUD(BaseTestCRUD):
    def get_object(self):
        return provisioner()

    def get_edit_data(self):
        return {
            'name': 'patched cluster',
            'engine': 'kqueen.engines.Dummy',
        }
