from flask import abort
from uuid import UUID


def get_object(object_class, pk):

    # read uuid
    if isinstance(pk, UUID):
        object_id = pk
    else:
        try:
            object_id = UUID(pk, version=4)
        except ValueError:
            abort(400)

    # load object
    try:
        obj = object_class.load(object_id)
    except NameError:
        abort(404)

    return obj
