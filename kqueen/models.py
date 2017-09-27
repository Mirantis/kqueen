#!/usr/bin/env python3

import etcd
import uuid
import json
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class EtcdOrm:
    def __init__(self, **kwargs):
        self.client = etcd.Client()
        self.prefix = kwargs.get('prefix', '/kqueen/obj/')


class Model:
    def __init__(self, *arfg, **kwargs):
        logger.debug('Model __init__')

        self._db = db

        # loop fiels and set it
        for a in self.get_field_names():
            field = getattr(self, a).__class__
            if hasattr(field, 'is_field') and kwargs.get(a):
                field_object = field()
                field_object.set_value(kwargs.get(a))
                setattr(self, a, field_object)

    @classmethod
    def get_model_name(cls):
        return cls.__name__.lower()

    @classmethod
    def get_db_prefix(cls):
        return '{}{}/'.format(db.prefix, cls.get_model_name())

    @classmethod
    def create(cls, **kwargs):
        """Create new object"""
        logger.debug('Model create')
        logger.debug(cls)
        logger.debug(kwargs)

        o = cls(**kwargs)

        return o

    @classmethod
    def load(cls, object_id):
        """Load object from database"""

        key = '{}{}'.format(cls.get_db_prefix(), str(object_id))

        try:
            response = db.client.read(key)
        except etcd.EtcdKeyNotFound:
            raise

        return cls.deserialize(response.value, key=key)

    @classmethod
    def deserialize(cls, serialized, **kwargs):
        deser = json.loads(serialized)
        o = cls(**deser)

        if kwargs.get('key'):
            o._key = kwargs.get('key')

        return o

    def get_field_names(self):
        """Return fields"""
        fields = []

        for a in self.__class__.__dict__.keys():
            field = getattr(self, a).__class__
            if hasattr(field, 'is_field'):
                fields.append(a)

        return fields

    def get_db_key(self):
        if not self.id:
            raise Exception('Missing object id')

        return '{}{}'.format(self.__class__.get_db_prefix(), self.id.serialize())

    def verify_id(self):
        if hasattr(self, 'id') and self.id and not self.id.empty():
            return self.id
        else:
            newid = uuid.uuid4()

            # TODO check id doesn't exists

            self.id.set_value(newid)

    def save(self):
        """Save object"""

        self.verify_id()

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

    def validate(self):
        return True

    def serialize(self):
        output = {}

        for field_name in self.get_field_names():
            field = getattr(self, field_name)
            serialized = field.serialize()
            if serialized:
                output[field_name] = serialized

        return json.dumps(output)

    def __str__(self):
        return '{} <{}>'.format(self.__class__.get_model_name(), self.id.serialize())

    def __eq__(self, other):
        return self.serialize() == other.serialize()


class Field:
    is_field = True

    def __init__(self, *args, **kwargs):
        self.value = None

    def set_value(self, value):
        self.value = value

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
    pass

db = EtcdOrm()


#
# Model definition
#

class Cluster(Model):
    id = IdField()
    name = StringField()
