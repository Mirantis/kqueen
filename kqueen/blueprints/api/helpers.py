from flask import abort
from uuid import UUID


def get_object(_class, pk):

    # read uuid
    try:
        object_id = UUID(pk, version=4)
    except ValueError:
        abort(400)

    # load object
    try:
        obj = _class.load(object_id)
    except NameError:
        abort(404)

    return obj
