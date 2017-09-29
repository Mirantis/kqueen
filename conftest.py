from kqueen.server import create_app
import pytest


@pytest.fixture
def app():
    app = create_app()
    return app
