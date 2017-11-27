from flask import jsonify
from flask.views import View
from flask import abort
from flask_jwt import _jwt_required, current_identity
from flask import current_app
from flask import request
from .helpers import get_object


class GenericView(View):
    def get_class(self):
        if hasattr(self, 'object_class'):
            return self.object_class
        else:
            raise NotImplementedError('Missing object_class variable or get_class')

    def get_content(self, *args, **kwargs):
        raise NotImplementedError

    def check_access(self):
        _jwt_required(current_app.config['JWT_DEFAULT_REALM'])

    def dispatch_request(self, *args, **kwargs):
        self.check_access()
        output = self.get_content(*args, **kwargs)

        return jsonify(output)


class GetView(GenericView):
    methods = ['GET']

    def get_content(self, *args, **kwargs):
        return get_object(self.get_class(), kwargs['pk'], current_identity)


class DeleteView(GenericView):
    methods = ['DELETE']

    def dispatch_request(self, *args, **kwargs):
        self.check_access()

        obj = get_object(self.get_class(), kwargs['pk'], current_identity)

        try:
            obj.delete()
        except:
            abort(500)

        return jsonify({'id': obj.id, 'state': 'deleted'})


class UpdateView(GenericView):
    methods = ['PATCH']

    def get_content(self, *args, **kwargs):
        return get_object(self.get_class(), kwargs['pk'], current_identity)

    def dispatch_request(self, *args, **kwargs):
        self.check_access()

        if not request.json:
            abort(400, description='JSON data expected')

        data = request.json
        if not isinstance(data, dict):
            abort(400)

        obj = get_object(self.get_class(), kwargs['pk'], current_identity)
        for key, value in data.items():
            setattr(obj, key, value)

        try:
            obj.save()
        except:
            abort(500)

        return super(UpdateView, self).dispatch_request(*args, **kwargs)


class ListView(GenericView):
    methods = ['GET']

    def get_content(self, *args, **kwargs):
        try:
            namespace = current_identity.namespace
        except AttributeError:
            namespace = None

        return list(self.get_class().list(namespace, return_objects=True).values())


class CreateView(GenericView):
    methods = ['POST']

    def save_object(self):
        self.obj.save()

    def after_save(self):
        pass

    def get_content(self, *args, **kwargs):
        return self.obj.get_dict(expand=True)

    def dispatch_request(self, *args, **kwargs):
        self.check_access()

        if not request.json:
            abort(400, description='JSON data expected')
        else:
            cls = self.get_class()

            try:
                namespace = current_identity.namespace
            except AttributeError:
                namespace = None

            self.obj = cls(namespace, **request.json)
            try:
                self.save_object()
                self.after_save()
            except Exception as e:
                current_app.logger.error(e)
                abort(500, description='Creation failed with: {}'.format(e))

            return super(CreateView, self).dispatch_request(*args, **kwargs)
