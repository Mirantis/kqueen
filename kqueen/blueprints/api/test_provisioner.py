from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import ProvisionerFixture
from kqueen.engines.__init__ import __all__ as all_engines
from pprint import pprint as print


class TestProvisionerCRUD(BaseTestCRUD):
    def get_object(self):
        return ProvisionerFixture()

    def get_edit_data(self):
        return {
            'name': 'patched cluster',
            'engine': 'kqueen.engines.Dummy',
        }

    def get_create_data(self):
        data = self.obj.get_dict()
        data['id'] = None
        data['owner'] = 'User:{}'.format(self.obj.owner.id)

        return data

    def test_provisioner_engines(self):
        url = url_for('api.provisioner_engine_list')

        response = self.client.get(url, headers=self.auth_header)
        print(response.json)

        assert response.status_code == 200
        assert isinstance(response.json, list)
        assert len(response.json) == len(all_engines)
