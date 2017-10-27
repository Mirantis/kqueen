from flask.json import JSONEncoder


class KqueenJSONEncoder(JSONEncoder):
    def default(self, obj):

        if hasattr(obj, 'get_dict'):
            return obj.get_dict()
        elif hasattr(obj, 'serialize'):
            return obj.serialize()

        try:
            return JSONEncoder.default(self, obj)
        except TypeError:
            print('Unserialized')
            print('class', obj.__class__)
            print('bases', dir(obj))
            print(type(obj))

            return {'__{}__'.format(obj.__class__.__name__): obj.__dict__}
