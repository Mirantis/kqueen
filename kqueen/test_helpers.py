import pytest
from kqueen.helpers import prefix_to_num


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
