from kqueen.auth import authenticate

import pytest

def test_nonexisting_user():
    """
    Try authenticate with non-existing user
    It is expected to return None but not fail
    """

    username = "non_existing_user"
    password = "password"

    result = authenticate(username, password)

    assert result is None
