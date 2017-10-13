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


model_kwargs = {'string': 'abc123', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'secret': 'pass'}
model_fields = ['id', 'string', 'json', 'secret']
model_serialized = '{"string": "abc123", "json": {"a": 1, "b": 2, "c": "tri"}, "secret": "pass"}'


@pytest.fixture
def create_object():
    model = create_model()
    return model(**model_kwargs)


class TestSave:
    def setup(self):
        model = create_model(required=True)
        self.obj = model()

    def test_model_invalid(self):
        assert not self.obj.validate()

    def test_save_raises(self):
        with pytest.raises(ValueError, match='Validation for model failed'):
            self.obj.save()

    def test_save_skip_validation(self):
        assert self.obj.save(validate=False)


class TestRequiredFields:
    @pytest.mark.parametrize('required', [True, False])
    def test_required(self, required):
        model = create_model(required=required)
        obj = model(**model_kwargs)

        assert obj.validate() != required


class TestModelInit:
    def setup(self):
        self.model = create_model()
        self.obj = self.model(**model_kwargs)

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

        assert hasattr(self.obj, attr_name)


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

    def test_serizalization(self, create_object):
        serialized = create_object.serialize()

        assert serialized == model_serialized

    def test_deserialization(self, create_object):
        object_class = create_object.__class__
        create_object.save()
        new_object = object_class.deserialize(create_object.serialize())

        assert new_object == create_object


class TestDuplicateId:
    def setup(self):
        self.model = create_model()

        self.obj1_kwargs = {'string': 'object 1', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'secret': 'pass'}
        self.obj2_kwargs = {'string': 'object 2', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'secret': 'pass'}

    def test_with_save(self):
        """"Save object are not same"""
        obj1 = self.model(**self.obj1_kwargs)
        obj2 = self.model(**self.obj2_kwargs)

        assert obj1 != obj2

        obj1.save()
        obj2.save()

        print(obj1.get_dict())
        print(obj2.get_dict())

        assert obj1.id != obj2.id
