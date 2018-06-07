from .exceptions import BackendError
from .exceptions import FieldError
from Crypto import Random
from Crypto.Cipher import AES
from datetime import datetime
from dateutil.parser import parse as du_parse
from flask import current_app
from kqueen.config import current_config

import base64
import etcd
import hashlib
import importlib
import json
import logging
import uuid

logger = logging.getLogger('kqueen_api')


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
        """Initialize Field object.

        Args:
            value: Set field value. This has higher priority than using attributes.

        Attributes:
            required (bool): Set field to be required before saving the model. Defaults to False.
            unique (bool): Set field to be unique within the Model before saving the model.
                           Defaults to False.
            value: Set field value.
        """
        # Field parameters
        self.required = kwargs.get('required', False)
        self.encrypted = kwargs.get('encrypted', False)
        self.default = kwargs.get('default', None)
        self.unique = kwargs.get('unique', False)

        # Value can be passed as args[0] or kwargs['value']
        if len(args) >= 1:
            self.value = args[0]
        else:
            self.value = kwargs.get('value', self._default_value())

        # Set block size for crypto
        self.bs = 16

    def _default_value(self):
        """Return default value directly or by calling return function."""
        if self.default is None:
            return
        if callable(self.default):
            return self.default()
        return self.default

    def on_create(self, **kwargs):
        """Optional action that should be run only on newly created objects."""
        pass

    def set_value(self, value, **kwargs):
        self.value = value

    def get_value(self):
        return self.value

    def dict_value(self):
        """Return field representation for API."""
        return self.get_value()

    def serialize(self):
        return str(self.value) if self.value is not None else None

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
        consistence of fields.

        Returns:
            Result of validation. True for success, False otherwise.
        """
        return True

    def _get_encryption_key(self):
        """Read encryption key and format it.

        Returns:
            Encryption key.
        """
        # Check for key
        config = current_config()
        key = config.get('SECRET_KEY')

        if key is None:
            raise Exception('Missing SECRET_KEY')

        # Calculate hash password
        return hashlib.sha256(key.encode('utf-8')).digest()[:self.bs]

    def _pad(self, s):
        return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)

    def _unpad(self, s):
        return s[:-ord(s[len(s) - 1:])]

    def encrypt(self):
        """Encrypt stored value."""
        serialized = self.serialize()

        if not self.encrypted:
            return serialized

        if serialized is not None:
            key = self._get_encryption_key()
            padded = self._pad(str(serialized))

            iv = Random.new().read(self.bs)
            suite = AES.new(key, AES.MODE_CBC, iv)
            encrypted = suite.encrypt(padded)
            encoded = base64.b64encode(iv + encrypted).decode('utf-8')

            return encoded

    def decrypt(self, crypted, **kwargs):
        if not self.encrypted:
            return self.deserialize(crypted, **kwargs)

        key = self._get_encryption_key()
        decoded = base64.b64decode(crypted)

        iv = decoded[:self.bs]
        suite = AES.new(key, AES.MODE_CBC, iv)
        decrypted = suite.decrypt(decoded[self.bs:])
        decrypted_decoded = decrypted.decode('utf-8')

        serialized = self._unpad(decrypted_decoded)

        self.deserialize(serialized, **kwargs)

    def __str__(self):
        return str(self.value)

    def __eq__(self, other):
        # The second is field
        if hasattr(other, 'is_field') and other.is_field:
            return self.value == other.value
        return self.value == other


class StringField(Field):
    pass


class BoolField(Field):
    def deserialize(self, serialized, **kwargs):
        if isinstance(serialized, str):
            value = json.loads(serialized)
            self.set_value(value, **kwargs)

    def set_value(self, value, **kwargs):
        if value is not None:
            if isinstance(value, bool):
                self.value = value
            else:
                self.deserialize(value)

    def serialize(self):
        if isinstance(self.value, bool):
            return json.dumps(self.value)


class IdField(Field):
    def set_value(self, value, **kwargs):
        """Don't serialize None."""
        self.value = str(value) if value is not None else value


class PasswordField(Field):
    def on_create(self):
        from kqueen.auth import encrypt_password
        self.value = encrypt_password(self.value)


class DatetimeField(Field):
    """Datetime is stored as UTC timestamp in DB and as naive datetime on instance."""

    def deserialize(self, serialized, **kwargs):
        # Convert to float if serialized is digit
        if isinstance(serialized, str) and serialized.isdigit():
            serialized = float(serialized)

        if isinstance(serialized, (float, int)):
            value = datetime.fromtimestamp(serialized)
            self.set_value(value, **kwargs)
        elif isinstance(serialized, str):
            value = du_parse(serialized)
            self.set_value(value, **kwargs)

    def set_value(self, value, **kwargs):
        if value and isinstance(value, datetime):
            self.value = value.replace(microsecond=0)
        else:
            self.deserialize(value)

    def serialize(self):
        return int(self.value.timestamp()) if isinstance(self.value, datetime) else None

    def dict_value(self):
        """Return API representation of value."""
        return self.value.isoformat() if self.value and isinstance(self.value, datetime) else None


class JSONField(Field):
    """JSON is stored as value."""

    def set_value(self, value, **kwargs):
        if isinstance(value, str):
            self.value = json.loads(value)
        elif isinstance(value, dict):
            self.value = value

    def serialize(self):
        return json.dumps(self.value) if isinstance(self.value, dict) else None


class RelationField(Field):
    """Store relations between models.

    Serialization format is `ModelName:object_id`.
    """

    def __init__(self, *args, **kwargs):
        super(RelationField, self).__init__(*args, **kwargs)
        self.remote_class_name = kwargs.get('remote_class_name')

    def serialize(self):
        model_name = self.value.__class__.__name__

        if self.remote_class_name and model_name != self.remote_class_name:
            msg = "Remote class mismatch, expected: {exp}, got: {got}".format(
                exp=self.remote_class_name,
                got=model_name
            )
            raise FieldError(msg)

        if self.value and self.__class__.is_field:
            return '{model_name}:{object_id}'.format(
                model_name=model_name,
                object_id=self.value.id,
            )

    def deserialize(self, serialized, **kwargs):
        """Deserialize relation to real object."""

        # TODO: CRITICAL make namespaced and check it
        if ':' in serialized:
            class_name, object_id = serialized.split(':')

            if self.remote_class_name and class_name != self.remote_class_name:
                msg = "Remote class mismatch, expected: {exp}, got: {got}".format(
                    exp=self.remote_class_name,
                    got=class_name
                )
                raise FieldError(msg)

            obj_class = self._get_related_class(class_name)

            obj = obj_class.load(kwargs.get('namespace'), object_id)
            self.set_value(obj, **kwargs)

    def _get_related_class(self, class_name):
        module = importlib.import_module('kqueen.models')
        return getattr(module, class_name)

    def validate(self):
        try:
            class_name = self.value.__class__.__name__
            selfid = self.value.id
        except Exception:
            return False

        return class_name and selfid

    def set_value(self, value, **kwargs):
        """Detect serialized format and deserialized according to format."""
        if isinstance(value, str) and ':' in value:
            self.deserialize(value, **kwargs)
        else:
            super(RelationField, self).set_value(value, **kwargs)


class ModelMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        newattributes = attributedict.copy()
        fields = {}

        # Loop attributes and set getters and setter for Fields
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
    """Parent class for all models."""
    id = IdField()  # id field is required for all models

    def __init__(self, ns=None, **kwargs):
        """Create model object.

        Args:
            ns (str): Namespace for created object. Required for namespaced objects.

        Attributes:
            **kwargs: Object attributes.
        """
        # Manage namespace
        if self.__class__.is_namespaced():
            self._object_namespace = ns

            if not self._object_namespace:
                raise BackendError('Missing namespace for class {}'.format(self.__class__.__name__))

        # Loop fields and set it
        for field_name, field in self.__class__.get_fields().items():
            field_class = field.__class__
            if hasattr(field_class, 'is_field'):
                field_object = field_class(**field.__dict__)
                field_object.set_value(kwargs.get(field_name, field_object._default_value()),
                                       namespace=ns)

                # Hash password field in case of new DB entry
                if kwargs.get('__create__', False):
                    field_object.on_create()

                setattr(self, '_{}'.format(field_name), field_object)

    @classmethod
    def get_model_name(cls):
        """Return lowercased name of the class."""
        return cls.__name__.lower()

    @classmethod
    def is_namespaced(cls):
        """Check whether model is namespaced or global.

        Returns:
            bool: True for namespaced models, False for global models.
        """
        return not (hasattr(cls, 'global_namespace') and cls.global_namespace)

    @classmethod
    def get_db_prefix(cls, namespace=None):
        """Calculate prefix for writing DB objects.

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
    def create(cls, ns, **kwargs):
        """Create a new object."""
        kwargs['__create__'] = True
        return cls(ns, **kwargs)

    @classmethod
    def list(cls, namespace, return_objects=True):
        """List objects in the database."""
        output = {}
        key = cls.get_db_prefix(namespace)

        try:
            directory = current_app.db.client.get(key)
        except etcd.EtcdKeyNotFound:
            return output

        # Don't allow iteration over children generator on empty directory.
        # More information is here: https://github.com/jplana/python-etcd/issues/54
        if not getattr(directory, '_children', []):
            return output

        for result in directory.children:
            output[result.key.replace(key, '')] = (
                cls.deserialize(result.value, namespace=namespace)
                if return_objects else None
            )

        return output

    @classmethod
    def load(cls, namespace, object_id):
        """Load object from database."""
        key = '{}{}'.format(cls.get_db_prefix(namespace), str(object_id))
        try:
            response = current_app.db.client.read(key)
            value = response.value
        except etcd.EtcdKeyNotFound:
            raise NameError('Object is not found')
        except Exception:
            raise

        return cls.deserialize(value, key=key, namespace=namespace)

    @classmethod
    def exists(cls, namespace, object_id):
        """Check if object exists."""
        try:
            cls.load(namespace, object_id)
            return True
        except NameError:
            return False

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        object_kwargs = {}
        # Deserialize toplevel dict and loop fields and deserialize them
        toplevel = json.loads(serialized)

        for field_name, field in cls.get_fields().items():
            field_class = field.__class__

            if hasattr(field_class, 'is_field') and toplevel.get(field_name) is not None:
                field_object = field_class(**field.__dict__)
                field_object.decrypt(toplevel[field_name], **kwargs)

                object_kwargs[field_name] = field_object.get_value()

        o = cls(kwargs.get('namespace'), **object_kwargs)

        if kwargs.get('key'):
            o._key = kwargs.get('key')

        return o

    @classmethod
    def get_fields(cls):
        """Return dict of fields and it classes."""
        return cls._fields

    @classmethod
    def get_field_names(cls):
        """Return list of field names."""
        return list(cls._fields.keys())

    def get_db_key(self):
        if not self.id:
            raise Exception('Missing object id')

        namespace = self._object_namespace if self.__class__.is_namespaced() else None
        return '{}{}'.format(self.__class__.get_db_prefix(namespace), self.id)

    def verify_id(self):
        if hasattr(self, 'id') and self.id is not None:
            return self.id
        else:
            newid = uuid.uuid4()

            # TODO check if id doesn't exists

            self.id = newid
            return self.id

    def save(self, validate=True, assign_id=True):
        """Save object to database.

        Hold lock during saving to avoid interruption into unique fields check.

        Attributes:
            validate (bool): Validate model before saving. Defaults to `True`.
            assign_id (bool): Assing id (if missing) before saving model. Defaults to `True`

        Return:
            bool: `True` if model was saved without errors, `False` otherwise.
        """
        with etcd.Lock(current_app.db.client, 'customer1'):
            if assign_id:
                self.verify_id()

            validation_status, validation_msg = self.validate()
            if validate and not validation_status:
                raise ValueError('Validation for model failed with: {}'.format(validation_msg))

            key = self.get_db_key()
            logger.debug('Writing {} to {}'.format(self, key))

            try:
                current_app.db.client.write(key, self.serialize())

                self._key = key
                return True
            except Exception:
                raise

    def delete(self):
        """Delete the object."""
        current_app.db.client.delete(self.get_db_key())

    def validate(self):
        """Validate the model object passes all requirements.

        Checks:
            * Required fields

        Returns:
            Validation result. `True` for passed, `False` for failed.
        """
        fields = self.__class__.get_field_names()
        for field in fields:
            hidden_field = '_{}'.format(field)
            field_object = getattr(self, hidden_field)

            # Validation
            # TODO: move to validate method of Field
            if field_object.required and field_object.value is None:
                return False, 'Required field {} is None'.format(field)

            if field_object.unique and field_object.value:
                namespace = self._object_namespace if self.is_namespaced() else self.namespace

                for k, v in self.list(namespace).items():
                    # Skip checking for uniqueness on object update
                    if getattr(v, 'id') == self.id:
                        continue
                    if getattr(v, field) == field_object.value:
                        return False, 'Field "{name}" should be unique'.format(name=field)

            if field_object.value and not field_object.validate():
                return False, 'Field {} validation failed'.format(field)

        return True, None

    def _expand(self, obj):
        expanded = obj.get_dict()
        for key, value in expanded.items():
            if hasattr(value, 'get_dict'):
                expanded[key] = self._expand(value)
        return expanded

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
                wr = self._expand(field.value)
            elif hasattr(field, 'dict_value'):
                wr = field.dict_value()
            else:
                wr = field.get_value()

            if wr is not None:
                output[field_name] = wr

        return output

    def serialize(self):
        serdict = {}
        for attr_name, attr in self.get_dict().items():
            value = getattr(self, '_{}'.format(attr_name)).encrypt()
            if value is not None:
                serdict[attr_name] = value

        return json.dumps(serdict)

    def __str__(self):
        return '{} <{}>'.format(self.__class__.get_model_name(), self.id)

    def __eq__(self, other):
        if hasattr(other, 'serialize'):
            return self.serialize() == other.serialize()
        else:
            return False

# TODO: implement autogenerated fields (generate them if missing)
# TODO: implement predefined values for fields
# TODO: use validation
# TODO: add is_saved method
# TODO: add load raw data method
