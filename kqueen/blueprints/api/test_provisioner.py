from .test_crud import BaseTestCRUD
from flask import url_for
from kqueen.conftest import provisioner
from uuid import uuid4

import pytest


class TestProvisionerCRUD(BaseTestCRUD):
    def get_object(self):
        return provisioner()

    def get_edit_data(self):
        return {
            'name': 'patched cluster',
            'engine': 'kqueen.engines.Dummy',
        }
