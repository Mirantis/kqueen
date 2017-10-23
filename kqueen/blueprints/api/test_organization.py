from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import organization
from uuid import uuid4

import pytest


class TestOrganizationCRUD(BaseTestCRUD):
    def get_object(self):
        return organization()

    def get_edit_data(self):
        return {
            'name': 'patched organization',
            'namespace': 'namespace123',
        }
