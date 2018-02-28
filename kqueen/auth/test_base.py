from .base import BaseAuth

import pytest


class TestBaseAuth:
    def setup(self):
        self.engine = BaseAuth()

    def test_verify_raises(self):

        with pytest.raises(NotImplementedError):
            self.engine.verify('username', 'password')

    def test_pass_kwargs(self):
        kwargs = {"test1": "abc", "test2": 123}

        self.engine = BaseAuth(**kwargs)

        for k, v in kwargs.items():
            assert getattr(self.engine, k) == v

    def test_kwargs_reserved(self):
        reserved = BaseAuth.RESERVED_KWARGS
        default_value = "abc"

        assert 'verify' in reserved

        kwargs = {k: default_value for k in reserved}

        self.engine = BaseAuth(**kwargs)

        for k in reserved:
            if hasattr(self.engine, k):
                assert getattr(self.engine, k) != default_value
