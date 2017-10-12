import etcd
import json
import logging
import uuid

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EtcdOrm:
    def __init__(self, **kwargs):
        self.client = etcd.Client()
        self.namespace = kwargs.get('namespace', 'default')
        self.prefix = kwargs.get('prefix', '/kqueen/obj/')


db = EtcdOrm()


class Field:
    is_field = True

    def __init__(self, *args, **kwargs):
        """Initialize Field object

        Attributes:
            required (bool): Set field to be required before saving the model. Defaults to False.

        """

        self.value = None
        self.required = kwargs.get('required', False)

    # waiting for @profesor to bring bright new idea
    # def __get__(self, obj, objtype):
    #     return self.value

    # def __set__(self, obj, val):
    #     self.value = val

    def set_value(self, value):
        self.value = value

    def get_value(self):
        return self.value

    def serialize(self):
        if self.value:
            return str(self.value)
        else:
            return None

    def empty(self):
        return self.value is None

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
    def set_value(self, value):
        """Don't serialize None"""
        if value:
            self.value = str(value)
        else:
            self.value = value


class SecretField(Field):
    pass


class JSONField(Field):
    """JSON is stored as value"""

    def set_value(self, value):
        if isinstance(value, str):
            self.value = json.loads(value)
        elif isinstance(value, dict):
            self.value = value

    def serialize(self):
        if self.value and isinstance(self.value, dict):
            return json.dumps(self.value)
        else:
            return None


class ModelMeta(type):
    def __new__(cls, clsname, superclasses, attributedict):
        newattributes = attributedict.copy()

        # loop attributes and set getters and setter for Fields
        for attr_name, attr in attributedict.items():
            attr_class = attr.__class__
            if hasattr(attr_class, 'is_field') and attr_class.is_field:
                name_hidden = '_{}'.format(attr_name)
                newattributes[name_hidden] = attr

                def fget(self, k=attr_name):
                    att = getattr(self, "_{}".format(k))
                    return att.get_value()

                def fset(self, value, k=attr_name):
                    att = getattr(self, "_{}".format(k))
                    att.set_value(value)

                newattributes[attr_name] = property(fget, fset)
                logger.debug('Setting {} to point to {}'.format(attr_name, name_hidden))

        return type.__new__(cls, clsname, superclasses, newattributes)


class Model:
    """Parent class for all models"""
    # id field is required for all models
    id = IdField()

    def __init__(self, *arfg, **kwargs):
        logger.debug('Model __init__')

        self._db = db

        # loop fields and set it
        for a in self.__class__.get_field_names():
            field_class = getattr(self, '_{}'.format(a)).__class__
            if hasattr(field_class, 'is_field') and kwargs.get(a):
                setattr(self, a, kwargs.get(a))
                logger.debug('Setting {} to {}'.format(a, kwargs.get(a)))

    @classmethod
    def get_model_name(cls):
        """Return lowercased name of the class"""

        return cls.__name__.lower()

    @classmethod
    def get_db_prefix(cls):
        """Calculate prefix for writing DB objects

        Returns:
            string: Database prefix

        Example:

            /kqueen/default/MyModel/

        """

        return '{prefix}{namespace}/{model}/'.format(
            prefix=db.prefix,
            namespace=db.namespace,
            model=cls.get_model_name(),
        )

    @classmethod
    def create(cls, **kwargs):
        """Create new object"""
        logger.debug('Model create')
        logger.debug(cls)
        logger.debug(kwargs)

        o = cls(**kwargs)

        return o

    @classmethod
    def list(cls, return_objects=True):
        """List objects in the database"""
        output = {}

        key = cls.get_db_prefix()

        try:
            directory = db.client.get(key)
        except etcd.EtcdKeyNotFound:
            return output

        for result in directory.children:
            if return_objects:
                output[result.key.replace(key, '')] = cls.deserialize(result.value)
            else:
                output[result.key.replace(key, '')] = None

        return output

    @classmethod
    def load(cls, object_id):
        """Load object from database"""

        key = '{}{}'.format(cls.get_db_prefix(), str(object_id))
        try:
            response = db.client.read(key)
            value = response.value
        except etcd.EtcdKeyNotFound:
            raise NameError('Object not found')
        except:
            raise

        return cls.deserialize(value, key=key)

    @classmethod
    def exists(cls, object_id):
        """Check if object exists"""

        try:
            cls.load(object_id)
            return True
        except NameError:
            return False

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        deser = json.loads(serialized)
        o = cls(**deser)

        if kwargs.get('key'):
            o._key = kwargs.get('key')

        return o

    @classmethod
    def get_field_names(cls):
        """Return list of field names"""
        fields = []

        for a in cls.__dict__.keys():
            field = getattr(cls, a).__class__
            if hasattr(field, 'is_field'):
                if a.startswith('_'):
                    a = a[1:]
                fields.append(a)

        return fields

    def get_db_key(self):
        if not self.id:
            raise Exception('Missing object id')

        return '{}{}'.format(self.__class__.get_db_prefix(), self.id)

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
            self._db.client.write(key, self.serialize())

            self._key = key
            return True
        except:
            raise

    def delete(self):
        """Delete the object"""

        self._db.client.delete(self.get_db_key())

    def validate(self) -> bool:
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

            if field_object.required and field_object.value is None:
                return False

        return True

    def get_dict(self):
        output = {}

        for field_name in self.__class__.get_field_names():
            field = getattr(self, field_name)
            if field:
                output[field_name] = field

        return output

    def serialize(self):

        return json.dumps(self.get_dict())

    def __str__(self):
        return '{} <{}>'.format(self.__class__.get_model_name(), self.id)

    def __eq__(self, other):
        return self.serialize() == other.serialize()

# TODO: implement required fields
# TODO: implement autogenerated fields (generete them if missing)
# TODO: implement unique field:w
# TODO: implement predefined values for fields
# TODO: use validation
