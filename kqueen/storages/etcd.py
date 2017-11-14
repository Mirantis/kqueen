import etcd
import json
import logging
import uuid
import importlib
from datetime import datetime
from kqueen.config import current_config
from flask import current_app
from .exceptions import BackendError

logger = logging.getLogger(__name__)


class EtcdBackend:
    def __init__(self, **kwargs):
        config = current_config()

        self.client = etcd.Client(
            host=config.get('ETCD_HOST', 'localhost'),
            port=int(config.get('ETCD_PORT', 4001)),
        )
        self.prefix = '{}/obj/'.format(config.get('ETCD_PREFIX', '/kqueen'))


class Field:
    is_field = True

    def __init__(self, *args, **kwargs):
        """Initialize Field object

        Attributes:
            required (bool): Set field to be required before saving the model. Defaults to False.

        """

        # TODO: pass value via args[0]

        self.value = kwargs.get('value', None)
        self.required = kwargs.get('required', False)

    def set_value(self, value, **kwargs):
        self.value = value

    def get_value(self):
        return self.value

    def dict_value(self):
        """Return field representation for API"""

        return self.get_value()

    def serialize(self):

        if self.value:
            return str(self.value)
        else:
            return None

    def deserialize(self, serialized, **kwargs):
        """
        This method is used for value deserialization. It is necessary to create instance first
        (with empty value) and then use `deserialize` method to fill the value.

        Default implementation in `Field` class is only passing value. It should be extended in
        specific field classes.

        Attributes:
            serialized (string): Serialized value of the field.
        """

        self.set_value(serialized, **kwargs)

    def empty(self):
        return self.value is None

    def validate(self):
        """
        This method is called before saving model and can be used to validate format or
        consitence of fields

        Returns:
            Result of validation. True for success, False otherwise.
        """
        return True

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        # second is field
        if hasattr(other, 'is_field') and other.is_field:
            return self.value == other.value
        else:
            return self.value == other


class StringField(Field):
    pass


class IdField(Field):
    def set_value(self, value, **kwargs):
        """Don't serialize None"""
        if value:
            self.value = str(value)
        else:
            self.value = value


class SecretField(Field):
    pass


class DatetimeField(Field):
    """
    Datetime is stored as UTC timestamp in DB and as naive datetime on instance.
    """

    def serialize(self):
        if self.value and isinstance(self.value, datetime):
            return int(self.value.timestamp())
        else:
            return None

    def deserialize(self, serialized, **kwargs):
        self.value = datetime.fromtimestamp(serialized)

    def dict_value(self):
        """Return API representation of value"""

        if self.value and isinstance(self.value, datetime):
            return self.value.isoformat()
        else:
            return None


class JSONField(Field):
    """JSON is stored as value"""

    def set_value(self, value, **kwargs):
        if isinstance(value, str):
            self.value = json.loads(value)
        elif isinstance(value, dict):
            self.value = value

    def serialize(self):
        if self.value and isinstance(self.value, dict):
            return json.dumps(self.value)
        else:
            return None


class RelationField(Field):
    """Store relations between models.

    Serialization format is `ModelName:object_id`.

    """

    # TODO: make Model property - limit relation objects only to one model

    def serialize(self):
        if self.value and self.__class__.is_field:
            return '{model_name}:{object_id}'.format(
                model_name=self.value.__class__.__name__,
                object_id=self.value.id,
            )
        else:
            return None

    def deserialize(self, serialized, **kwargs):
        """Deserialize relation to real object"""

        if ':' in serialized:
            class_name, object_id = serialized.split(':')

            obj_class = self._get_related_class(class_name)
            # TODO: CRITICAL make namespaced and check it

            obj = obj_class.load(kwargs.get('namespace'), object_id)
            self.set_value(obj, **kwargs)

    def _get_related_class(self, class_name):
        module = importlib.import_module('kqueen.models')

        return getattr(module, class_name)

    def validate(self):
        try:
            class_name = self.value.__class__.__name__
            selfid = self.value.id
        except:
            return False

        return class_name and selfid

    def set_value(self, value, **kwargs):
        """Detect serialized format and deserialized according to format."""
        if isinstance(value, str) and ':' in value:
            # deserialize
            self.deserialize(value, **kwargs)
        else:
            super(RelationField, self).set_value(value, **kwargs)


class ModelMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        newattributes = attributedict.copy()
        fields = {}

        # loop attributes and set getters and setter for Fields
        for attr_name, attr in attributedict.items():
            attr_class = attr.__class__
            if hasattr(attr_class, 'is_field') and attr_class.is_field:
                name_hidden = '_{}'.format(attr_name)
                fields[attr_name] = attr

                def fget(self, k=attr_name):
                    att = getattr(self, "_{}".format(k))
                    return att.get_value()

                def fset(self, value, k=attr_name):
                    att = getattr(self, "_{}".format(k))
                    att.set_value(value)

                newattributes[attr_name] = property(fget, fset)
                logger.debug('Setting {} to point to {}'.format(attr_name, name_hidden))

        newattributes['_fields'] = fields

        return type.__new__(cls, clsname, superclasses, newattributes)


class Model:
    """Parent class for all models"""
    # id field is required for all models
    id = IdField()

    def __init__(self, ns=None, **kwargs):
        """
        Create model object.

        Args:
            ns (str): Namespace for created object. Required for namespaced objects.

        Attributes:
            **kwargs: Object attributes.

        """

        # manage namespace
        if self.__class__.is_namespaced():
            self._object_namespace = ns

            if not self._object_namespace:
                raise BackendError('Missing namespace for class {}'.format(self.__class__.__name__))

        # loop fields and set it
        for field_name, field in self.__class__.get_fields().items():
            field_class = field.__class__
            if hasattr(field_class, 'is_field'):
                field_object = field_class(**field.__dict__)
                field_object.set_value(kwargs.get(field_name), namespace=ns)
                setattr(self, '_{}'.format(field_name), field_object)

    @classmethod
    def get_model_name(cls):
        """Return lowercased name of the class"""

        return cls.__name__.lower()

    @classmethod
    def is_namespaced(cls):
        """
        Check if model is namespaced or global.

        Returns:
            bool: True for namespaced models, False for global models.
        """
        if hasattr(cls, 'global_namespace') and cls.global_namespace:
            return False
        else:
            return True

    @classmethod
    def get_db_prefix(cls, namespace=None):
        """Calculate prefix for writing DB objects

        Returns:
            string: Database prefix

        Example:

            /kqueen/default/MyModel/

        """

        if cls.is_namespaced():
            if not namespace:
                raise BackendError('Missing namespace for class {}'.format(cls.__name__))
        else:
            namespace = 'global'

        return '{prefix}{namespace}/{model}/'.format(
            prefix=current_app.db.prefix,
            namespace=namespace,
            model=cls.get_model_name(),
        )

    @classmethod
    def create(cls, namespace, **kwargs):
        """Create new object"""

        o = cls(namespace, **kwargs)

        return o

    @classmethod
    def list(cls, namespace, return_objects=True):
        """List objects in the database"""
        output = {}

        key = cls.get_db_prefix(namespace)

        try:
            directory = current_app.db.client.get(key)
        except etcd.EtcdKeyNotFound:
            return output

        for result in directory.children:
            if return_objects:
                output[result.key.replace(key, '')] = cls.deserialize(result.value, namespace=namespace)
            else:
                output[result.key.replace(key, '')] = None

        return output

    @classmethod
    def load(cls, namespace, object_id):
        """Load object from database"""

        key = '{}{}'.format(cls.get_db_prefix(namespace), str(object_id))
        try:
            response = current_app.db.client.read(key)
            value = response.value
        except etcd.EtcdKeyNotFound:
            raise NameError('Object not found')
        except:
            raise

        return cls.deserialize(value, key=key, namespace=namespace)

    @classmethod
    def exists(cls, namespace, object_id):
        """Check if object exists"""

        try:
            cls.load(namespace, object_id)
            return True
        except NameError:
            return False

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        object_kwargs = {}

        # deserialize toplevel dict and loop fields and deserialize them
        toplevel = json.loads(serialized)

        for field_name, field in cls.get_fields().items():
            field_class = field.__class__
            if hasattr(field_class, 'is_field') and toplevel.get(field_name):
                field_object = field_class(**field.__dict__)
                field_object.deserialize(toplevel[field_name], **kwargs)

                object_kwargs[field_name] = field_object.get_value()

        o = cls(kwargs.get('namespace'), **object_kwargs)

        if kwargs.get('key'):
            o._key = kwargs.get('key')

        return o

    @classmethod
    def get_fields(cls):
        """Return dict of fields and it classes"""

        return cls._fields

    @classmethod
    def get_field_names(cls):
        """Return list of field names"""

        return list(cls._fields.keys())

    def get_db_key(self):
        if not self.id:
            raise Exception('Missing object id')

        if self.__class__.is_namespaced():
            namespace = self._object_namespace
        else:
            namespace = None

        return '{}{}'.format(self.__class__.get_db_prefix(namespace), self.id)

    def verify_id(self):
        if hasattr(self, 'id') and self.id is not None:
            return self.id
        else:
            newid = uuid.uuid4()

            # TODO check id doesn't exists

            self.id = newid
            return self.id

    def save(self, validate=True, assign_id=True):
        """Save object to database


        Attributes:
            validate (bool): Validate model before saving. Defaults to `True`.
            assign_id (bool): Assing id (if missing) before saving model. Defaults to `True`

        Return:
            bool: `True` if model was saved without errors, `False` otherwise.

        """

        if assign_id:
            self.verify_id()

        if validate and not self.validate():
            raise ValueError('Validation for model failed')

        key = self.get_db_key()
        logger.debug('Writing {} to {}'.format(self, key))

        try:
            current_app.db.client.write(key, self.serialize())

            self._key = key
            return True
        except:
            raise

    def delete(self):
        """Delete the object"""

        current_app.db.client.delete(self.get_db_key())

    def validate(self):
        """Validate the model object pass all requirements

        Checks:
            * Required fields

        Returns:
            Validation result. `True` for passed, `False` for failed.
        """

        fields = self.__class__.get_field_names()
        for field in fields:
            hidden_field = '_{}'.format(field)
            field_object = getattr(self, hidden_field)

            # validation
            # TODO: move to validate method of Field
            if field_object.required and field_object.value is None:
                return False

            if field_object.value and not field_object.validate():
                return False

        return True

    def get_dict(self, expand=False):
        """Return object properties represented by dict.

        Attributes:
            expand (bool): Expand properties to dict (if possible).

        Returns:
            Dict with object properties
        """

        output = {}

        for field_name in self.__class__.get_field_names():
            field = getattr(self, '_{}'.format(field_name))

            if expand and hasattr(field.value, 'get_dict'):
                wr = field.value.get_dict()
            elif hasattr(field, 'dict_value'):
                wr = field.dict_value()
            else:
                wr = field.get_value()

            if wr:
                output[field_name] = wr

        return output

    def serialize(self):
        serdict = {}
        for attr_name, attr in self.get_dict().items():
            serdict[attr_name] = getattr(self, '_{}'.format(attr_name)).serialize()

        return json.dumps(serdict)

    def __str__(self):
        return '{} <{}>'.format(self.__class__.get_model_name(), self.id)

    def __eq__(self, other):
        if hasattr(other, 'serialize'):
            return self.serialize() == other.serialize()
        else:
            return False

# TODO: implement autogenerated fields (generete them if missing)
# TODO: implement unique field:w
# TODO: implement predefined values for fields
# TODO: use validation
# TODO: add is_saved method
# TODO: add load raw data method
