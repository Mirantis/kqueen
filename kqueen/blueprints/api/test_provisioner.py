from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import provisioner
from kqueen.engines.__init__ import __all__ as all_engines
from pprint import pprint as print


class TestProvisionerCRUD(BaseTestCRUD):
    def get_object(self):
        return provisioner()

    def get_edit_data(self):
        return {
            'name': 'patched cluster',
            'engine': 'kqueen.engines.Dummy',
        }

    def test_provision_engines(self):
        url = url_for('api.provisioner_engine_list')

        response = self.client.get(url, headers=self.auth_header)
        print(response.json)

        assert isinstance(response.json, list)
        assert len(response.json) == len(all_engines)
