from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.config import current_config
from kqueen.conftest import organization

config = current_config()


class TestOrganizationCRUD(BaseTestCRUD):
    def get_object(self):
        return organization()

    def get_edit_data(self):
        return {
            'name': 'patched organization',
            'namespace': 'namespace123',
        }

    def test_policy(self):
        url = url_for('api.organization_policy', pk=self.obj.id)

        policies = config.get('DEFAULT_POLICIES', {})
        if hasattr(self.obj, 'policy') and self.obj.policy:
            policies.update(self.obj.policy)

        response = self.client.get(
            url,
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json == policies
