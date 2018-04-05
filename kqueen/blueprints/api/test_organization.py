from kqueen.config.utils import kqueen_config
from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import organization

import pytest


class TestOrganizationCRUD(BaseTestCRUD):
    def get_object(self):
        return organization()

    def get_edit_data(self):
        return {
            'name': 'patched organization',
            'namespace': 'namespace123',
        }

    def test_crud_delete(self):
        deletable, remaining = self.obj.is_deletable()
        response = self.client.delete(
            self.urls['delete'],
            headers=self.auth_header,
        )

        if deletable:
            assert response.status_code == 200
            with pytest.raises(NameError, message='Object not found'):
                self.obj.__class__.load(
                    self.namespace,
                    self.obj.id,
                )
        else:
            assert response.status_code == 500
            assert isinstance(remaining, list) and remaining

    def test_policy(self):
        url = url_for('api.organization_policy', pk=self.obj.id)

        policies = kqueen_config.get('DEFAULT_POLICIES', {})
        if hasattr(self.obj, 'policy') and self.obj.policy:
            policies.update(self.obj.policy)

        response = self.client.get(
            url,
            headers=self.auth_header,
            content_type='application/json',
        )

        assert response.status_code == 200
        assert response.json == policies
