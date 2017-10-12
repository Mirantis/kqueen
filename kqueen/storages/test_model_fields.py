from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import SecretField
from kqueen.storages.etcd import StringField
from kqueen.storages.etcd import ModelMeta

import pytest


def create_model(required=False):
    class TestModel(Model, metaclass=ModelMeta):
        id = IdField(required=required)
        string = StringField(required=required)
        json = JSONField(required=required)
        secret = SecretField(required=required)

    return TestModel


model_kwargs = {'string': 'abc123', 'json': {'a': 1, 'b': 2, 'c': 'tři'}, 'secret': 'pass'}
model_fields = ['id', 'string', 'json', 'secret']


@pytest.fixture
def create_object():
    model = create_model()
    return model(**model_kwargs)


class TestRequiredFields:
    @pytest.mark.skip('not implemented')
    def test_required(self):
        model = create_model(required=True)
        obj = model()

        assert not obj.validate()


class TestModelInit:
    def setup(self):
        self.model = create_model()

    @pytest.mark.parametrize('field_name,field_value', model_kwargs.items())
    def test_init_string(self, field_name, field_value):
        """Initialization of new models is properly setting properties"""

        kwargs = {field_name: field_value}
        obj = self.model(**kwargs)

        assert getattr(obj, field_name) == field_value

    @pytest.mark.parametrize('attr', model_fields)
    @pytest.mark.parametrize('group', ['', '_'])
    def test_field_property_getters(self, attr, group):
        attr_name = '{}{}'.format(group, attr)

        assert hasattr(self.model, attr_name)


class TestGetFieldNames:
    def test_get_field_names(self, create_object):
        field_names = create_object.__class__.get_field_names()
        req = ['id', 'string', 'json', 'secret']

        assert field_names == req

    def test_get_dict(self, create_object):
        print(create_object.__dict__)
        print(create_object.get_dict())


class TestFieldSetGet:
    """Validate getters and setters for fields"""
    @pytest.mark.parametrize('field_name', model_kwargs.keys())
    def test_get_fields(self, field_name, create_object):
        at = getattr(create_object, field_name)
        req = model_kwargs[field_name]

        assert at == req

    @pytest.mark.parametrize('field_name', model_kwargs.keys())
    def test_set_fields(self, field_name):
        model_class = create_model()
        obj = model_class()
        setattr(obj, field_name, model_kwargs[field_name])

        print(obj.get_dict())

        assert getattr(obj, field_name) == model_kwargs[field_name]
        assert obj.get_dict()[field_name] == model_kwargs[field_name]
        assert getattr(obj, '_{}'.format(field_name)).get_value() == model_kwargs[field_name]


class TestModelAddId:
    def test_id_added(self, create_object):
        obj = create_object

        assert obj.id is None
        assert obj.verify_id()
        assert obj.id is not None

        create_object.save()


class TestSerialization:
    """Serialization and deserialization create same objects"""

    @pytest.mark.skip('Finish serialization')
    def test_serizalization(self, create_object):
        print(create_object)
        print(create_object)
        # TODO: finish serialization test
