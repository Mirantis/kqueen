from kqueen.helpers import camel_split
from kqueen.helpers import prefix_to_num

import pytest


@pytest.mark.parametrize('st,req', [
    ('0', 0),
    ('1G', 1000000000),
    ('1Gi', 1073741824),
    ('1 Gi', 1073741824),
    ('100', 100),
    ('100m', 0.1),
])
def test_prefix_to_num(st, req):
    assert prefix_to_num(st) == req


@pytest.mark.parametrize('st,req', [
    ('CamelCase', ['Camel', 'Case']),
    ('camelcase', ['camelcase']),
])
def test_camel_split(st, req):
    assert camel_split(st) == req
