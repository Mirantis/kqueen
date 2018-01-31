from kqueen.serializers import KqueenJSONEncoder

import pytest


class SerByMethod:
    def serialize(self):
        return "ser"


class NotSerializable:
    pass


@pytest.mark.parametrize('obj', [
    SerByMethod()
])
def test_serializer(obj):
    enc = KqueenJSONEncoder()

    assert enc.default(obj) == 'ser'


def test_not_serializable(capsys):
    obj = NotSerializable()
    enc = KqueenJSONEncoder()

    enc.default(obj)

    out, err = capsys.readouterr()
    assert "Unserialized" in out
