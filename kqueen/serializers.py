from flask.json import JSONEncoder


class CustomJSONEncoder(JSONEncoder):
    def default(self, obj):

        try:

            return JSONEncoder.default(self, obj)
        except TypeError:
            print('Unserialized')
            print(obj.__class__)
            print(type(obj))
            return {'__{}__'.format(obj.__class__.__name__): obj.__dict__}
