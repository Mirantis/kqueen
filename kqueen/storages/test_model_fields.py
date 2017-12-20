from kqueen.storages.etcd import BoolField
from kqueen.storages.etcd import DatetimeField
from kqueen.storages.etcd import Field
from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import JSONField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import ModelMeta
from kqueen.storages.etcd import PasswordField
from kqueen.storages.etcd import RelationField
from kqueen.storages.etcd import StringField
from kqueen.storages.exceptions import BackendError

import datetime
import pytest
import itertools


def create_model(required=False, global_ns=False, encrypted=False):
    class TestModel(Model, metaclass=ModelMeta):
        if global_ns:
            global_namespace = global_ns

        id = IdField(required=required, encrypted=encrypted)
        string = StringField(required=required, encrypted=encrypted)
        json = JSONField(required=required, encrypted=encrypted)
        password = PasswordField(required=required, encrypted=encrypted)
        relation = RelationField(required=required, encrypted=encrypted)
        datetime = DatetimeField(required=required, encrypted=encrypted)
        boolean = BoolField(required=required, encrypted=encrypted)

        _required = required
        _global_ns = global_ns
        _encrypted = encrypted

        if _global_ns:
            _namespace = None
        else:
            _namespace = namespace

    return TestModel


utcnow = datetime.datetime(1989, 11, 17)

model_kwargs = {'string': 'abc123', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'password': 'pass', 'datetime': utcnow, 'boolean': True}
model_kwargs_dict = {'string': 'abc123', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'password': 'pass', 'datetime': utcnow.isoformat(), 'boolean': True}
model_fields = ['id', 'string', 'json', 'password', 'relation', 'datetime', 'boolean']
namespace = 'test'


def model_serialized(related=None):
    if related:
        return (
            '{{"string": "abc123", "json": "{{\\"a\\": 1, \\"b\\": 2, \\"c\\": \\"tri\\"}}", '
            '"password": "pass", "relation": "{related_class}:{related_id}", "datetime": {date_timestamp}, '
            '"boolean": "true"}}'.format(
                related_class=related.__class__.__name__,
                related_id=related.id,
                date_timestamp=int(utcnow.timestamp())
            )
        )
    else:
        return (
            '{{"string": "abc123", "json": "{\\"a\\": 1, \\"b\\": 2, \\"c\\": \\"tri\\"}", '
            '"password": "pass", "datetime": {date_timestamp}, "boolean": "true"}}'.format(
                date_timestamp=int(utcnow.timestamp()),
            )
        )


@pytest.fixture(params=itertools.product([True, False], repeat=3))
def get_object(request):
    return create_object(*request.param)


@pytest.fixture(params=itertools.product([True, False], repeat=3))
def get_model(request):
    return create_model(*request.param)


def create_object(required=False, global_ns=False, encrypted=False):
    model = create_model()

    obj1 = model(namespace, **model_kwargs)
    obj2 = model(namespace, **model_kwargs)

    obj2.save()

    obj1.relation = obj2

    return obj1


class TestModelInit:
    def setup(self):
        self.model = create_model()
        self.obj = self.model(namespace, **model_kwargs)

    @pytest.mark.parametrize('field_name,field_value', model_kwargs.items())
    def test_init_string(self, field_name, field_value):
        """Initialization of new models is properly setting properties"""

        kwargs = {field_name: field_value}
        obj = self.model(namespace, **kwargs)

        assert getattr(obj, field_name) == field_value

    @pytest.mark.parametrize('attr', model_fields)
    @pytest.mark.parametrize('group', ['', '_'])
    def test_field_property_getters(self, attr, group):
        attr_name = '{}{}'.format(group, attr)

        assert hasattr(self.obj, attr_name)


class TestSave:
    def setup(self):
        model = create_model(required=True)
        self.obj = model(namespace)

    def test_model_invalid(self):
        assert not self.obj.validate()

    def test_save_raises(self):
        with pytest.raises(ValueError, match='Validation for model failed'):
            self.obj.save()

    def test_save_skip_validation(self):
        assert self.obj.save(validate=False)


class TestModelAddId:
    def test_id_added(self, get_object):
        obj = get_object

        assert obj.id is None
        assert obj.verify_id()
        assert obj.id is not None

        obj.save()


class TestRequiredFields:
    @pytest.mark.parametrize('required', [True, False])
    def test_required(self, required):
        model = create_model(required=required)
        obj = model(namespace, **model_kwargs)

        assert obj.validate() != required


class TestGetFieldNames:
    def test_get_field_names(self, get_object):
        field_names = get_object.__class__.get_field_names()
        req = model_fields

        assert set(field_names) == set(req)

    def test_get_dict(self, get_object):
        dicted = get_object.get_dict()

        assert isinstance(dicted, dict)


class TestFieldSetGet:
    """Validate getters and setters for fields"""
    @pytest.mark.parametrize('field_name', model_kwargs.keys())
    def test_get_fields(self, field_name, get_object):
        at = getattr(get_object, field_name)
        req = model_kwargs[field_name]

        assert at == req

    @pytest.mark.parametrize('field_name', model_kwargs.keys())
    def test_set_fields(self, field_name):
        model_class = create_model()
        obj = model_class(namespace)
        setattr(obj, field_name, model_kwargs[field_name])

        assert getattr(obj, field_name) == model_kwargs[field_name]
        assert obj.get_dict()[field_name] == model_kwargs_dict[field_name]
        assert getattr(obj, '_{}'.format(field_name)).get_value() == model_kwargs[field_name]


class TestSerialization:
    """Serialization and deserialization create same objects"""

    def test_serizalization(self, get_object):
        serialized = get_object.serialize()

        assert serialized == model_serialized(related=get_object.relation)

    def test_deserialization(self, get_object, monkeypatch):
        def fake(self, class_name):
            return get_object.__class__

        monkeypatch.setattr(RelationField, '_get_related_class', fake)

        object_class = get_object.__class__
        get_object.save()
        new_object = object_class.deserialize(get_object.serialize(), namespace=namespace)

        assert new_object.get_dict() == get_object.get_dict()


class TestGetDict:
    """Verify objects are serialized properly"""

    def setup(self):
        self.obj1 = create_object()
        self.obj1.string = 'obj1'
        self.obj2 = create_object()
        self.obj1.string = 'obj2'

        self.obj1.save()
        self.obj2.save()

        self.obj1.relation = self.obj2

    def test_get_dict(self):
        dicted = self.obj1.get_dict(expand=False)

        assert dicted['relation'] == self.obj2

    def test_get_dict_expand(self):
        dicted = self.obj1.get_dict(expand=True)

        assert isinstance(dicted['relation'], dict)
        assert dicted['relation'] == self.obj2.get_dict(expand=True)


class TestDuplicateId:
    def setup(self):
        self.model = create_model()

        self.obj1_kwargs = {'string': 'object 1', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'password': 'pass'}
        self.obj2_kwargs = {'string': 'object 2', 'json': {'a': 1, 'b': 2, 'c': 'tri'}, 'password': 'pass'}

    def test_with_save(self):
        """"Save object are not same"""
        obj1 = self.model(namespace, **self.obj1_kwargs)
        obj2 = self.model(namespace, **self.obj2_kwargs)

        assert obj1 != obj2

        obj1.save()
        obj2.save()

        print(obj1.get_dict())
        print(obj2.get_dict())

        assert obj1.id != obj2.id


class TestFieldSetValues:
    def setup(self):
        self.value = 'abc123'

    def test_create_by_args(self):
        field = Field(self.value)

        assert field.value == self.value

    def test_create_by_kwargs(self):
        field = Field(value=self.value)

        assert field.value == self.value

    def test_create_by_both(self):
        field = Field('args_value', value='kwargs_value')

        assert field.value == 'args_value'

#
# Relation Field
#


class TestRelationField:
    def setup(self):
        self.obj1 = create_object()
        self.obj1.name = 'obj1'
        self.obj2 = create_object()
        self.obj2.name = 'obj2'

        self.obj1.save()
        self.obj2.save()

        self.obj1.relation = self.obj2

    def test_relation_attrs(self):
        assert self.obj1.relation == self.obj2
        assert self.obj1._relation.value == self.obj2

    def test_relation_serialization(self):
        ser = self.obj1._relation.serialize()
        req = '{model_name}:{object_id}'.format(
            model_name=self.obj2.__class__.__name__,
            object_id=self.obj2.id
        )

        assert ser == req

    def test_relation_loading(self, monkeypatch):
        def fake_related_class(their, class_name):
            return self.obj1.__class__

        monkeypatch.setattr(RelationField, '_get_related_class', fake_related_class)

        self.obj1.save()
        loaded = self.obj1.__class__.load(namespace, self.obj1.id)

        assert isinstance(loaded, self.obj1.__class__)
        assert hasattr(loaded, 'relation')
        assert loaded.relation == self.obj2


class TestNamespaces:
    def setup(self):
        self.class_namespaced = create_model(False, False)
        self.class_global = create_model(False, True)

    def test_is_namespaced(self):
        assert self.class_namespaced.is_namespaced()
        assert not self.class_global.is_namespaced()

    def test_write_with_namespace(self):
        obj = self.class_namespaced(namespace, **model_kwargs)

        assert obj.save()
        assert obj._object_namespace == namespace

    def test_raise_missing_namespace(self):
        with pytest.raises(BackendError):
            self.class_namespaced(**model_kwargs)

    @pytest.mark.parametrize('ns,req_ns', [
        ('test', 'test')
    ])
    def test_get_db_prefix(self, ns, req_ns):
        cls = self.class_namespaced
        prefix = cls.get_db_prefix(ns)

        req = '/{app_prefix}/obj/{namespace}/{class_name}/'.format(
            app_prefix='kqueen_test',
            namespace=req_ns,
            class_name=cls.get_model_name(),
        )

        assert req == prefix

    def test_get_db_prefix_raises_on_missing_ns(self):
        cls = self.class_namespaced

        with pytest.raises(BackendError, match='Missing namespace'):
            cls.get_db_prefix(None)


datetime_sample = datetime.datetime(2007, 12, 6, 16, 29, 43)


class TestDateTimeField:
    def setup(self):
        self.datetime = datetime_sample
        self.field = DatetimeField()

    def test_serialization(self):
        req = int(self.datetime.timestamp())
        self.field.set_value(self.datetime)

        assert self.field.serialize() == req

    def test_serialization_none(self):
        self.field.set_value(None)

        assert self.field.serialize() is None

    @pytest.mark.parametrize('serialized, req', [
        (datetime_sample.timestamp(), datetime_sample),
        (int(datetime_sample.timestamp()), datetime_sample),
        (datetime_sample.isoformat(), datetime_sample),
    ])
    def test_deserialization(self, serialized, req):
        self.field.deserialize(serialized)

        assert self.field.value == req

    def test_dict_value_returns_isoformat(self):
        self.field.set_value(self.datetime)

        assert self.field.dict_value() == self.field.value.isoformat()


class TestBoolField:
    def setup(self):
        self.boolean = False
        self.field = BoolField()

    def test_serialization(self):
        req = 'false'
        self.field.set_value(self.boolean)

        assert self.field.serialize() == req

    def test_serialization_none(self):
        self.field.set_value(None)

        assert self.field.serialize() is None

    @pytest.mark.parametrize('serialized, req', [
        ('false', False),
        ('true', True),
    ])
    def test_deserialization(self, serialized, req):
        self.field.deserialize(serialized)

        assert self.field.value == req

    def test_dict_value_returns_boolean(self):
        self.field.set_value(self.boolean)

        assert self.field.dict_value() == self.boolean


#
# Encryption
#
class TestFieldEncryption:
    def test_get_encryption_key(self, get_model):

        obj = get_model(get_model._namespace, **model_kwargs)

        field = obj._string
        KEY_LENGTH = obj._string.bs
        key = field._get_encryption_key()

        assert len(key) == KEY_LENGTH

    @pytest.mark.parametrize('field_name, field_value', model_kwargs.items())
    def test_encryption_and_decryption(self, field_name, field_value):

        cls = create_model(False, False, True)
        obj = cls(namespace, **model_kwargs)

        field = getattr(obj, '_{}'.format(field_name))
        field.set_value(field_value)
        assert field.encrypted

        # encryption
        encrypted = field.encrypt()

        assert isinstance(encrypted, str)

        # decryption
        field.set_value(None)
        field.decrypt(encrypted)

        assert field.value == field_value

    @pytest.mark.parametrize('field_name, field_value', model_kwargs.items())
    def test_serialized_model_dont_contain_value(self, field_name, field_value):
        cls = create_model(False, False, True)
        obj = cls(namespace, **model_kwargs)

        serialized = obj.serialize()
        field = getattr(obj, '_{}'.format(field_name))

        assert '"{}"'.format(field.value) not in serialized
        assert '"{}"'.format(field.serialize()) not in serialized
