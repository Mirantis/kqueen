from flask import abort
from uuid import UUID


def get_object(object_class, pk, user=None):

    # read uuid
    if isinstance(pk, UUID):
        object_id = pk
    else:
        try:
            object_id = UUID(pk, version=4)
        except ValueError:
            abort(400)

    # read namespace for user
    try:
        namespace = user.namespace
    except AttributeError:
        namespace = None

    # load object
    try:
        obj = object_class.load(object_id, namespace)
    except NameError:
        abort(404)

    return obj
