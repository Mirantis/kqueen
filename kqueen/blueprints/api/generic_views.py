from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask.views import View
from flask_jwt import _jwt_required, current_identity, JWTError
from kqueen.auth import is_authorized
from .helpers import get_object


class GenericView(View):
    obj = None

    def get_class(self):
        if hasattr(self, 'object_class'):
            return self.object_class
        else:
            raise NotImplementedError('Missing object_class variable or get_class')

    def get_content(self, *args, **kwargs):
        raise NotImplementedError

    def check_authorization(self):
        # get view class
        try:
            _class = self.get_class()
        except NotImplementedError:
            return

        # get user data
        if current_identity:
            user = current_identity.get_dict()
            organization = current_identity.organization
        else:
            return

        # form policy key
        policy = '{}:{}'.format(_class.__name__.lower(), self.action)
        # get policies and update them with organization level overrides
        policies = current_app.config.get('DEFAULT_POLICIES', {})
        if hasattr(organization, 'policies') and organization.policies:
            policies.update(organization.policies)
        policy_value = policies.get(policy, None)

        # evaluate user permissions
        # if there are multiple objects, filter out those which current user
        # doesn't have access to
        if isinstance(self.obj, list):
            allowed = []
            for obj in self.obj:
                if is_authorized(user, policy_value, resource=obj):
                    allowed.append(obj)
            self.obj = allowed
        # if there is single object raise if user doesn't have access to it
        elif policy_value and user:
            if not is_authorized(user, policy_value, resource=self.obj):
                raise JWTError('Insufficient permissions',
                               'Your user account is lacking the necessary '
                               'permissions to perform this operation')

    def check_authentication(self):
        _jwt_required(current_app.config['JWT_DEFAULT_REALM'])

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)
        self.check_authorization()
        output = self.get_content(*args, **kwargs)

        return jsonify(output)

    def set_object(self, *args, **kwargs):
        pass


class GetView(GenericView):
    methods = ['GET']
    action = 'get'

    def set_object(self, *args, **kwargs):
        self.obj = get_object(self.get_class(), kwargs['pk'], current_identity)

    def get_content(self, *args, **kwargs):
        return self.obj


class DeleteView(GenericView):
    methods = ['DELETE']
    action = 'delete'

    def set_object(self, *args, **kwargs):
        self.obj = get_object(self.get_class(), kwargs['pk'], current_identity)

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)
        self.check_authorization()

        try:
            self.obj.delete()
        except Exception:
            abort(500)

        return jsonify({'id': self.obj.id, 'state': 'deleted'})


class UpdateView(GenericView):
    methods = ['PATCH']
    action = 'update'

    def set_object(self, *args, **kwargs):
        self.obj = get_object(self.get_class(), kwargs['pk'], current_identity)

    def get_content(self, *args, **kwargs):
        return self.obj

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()

        if not request.json:
            abort(400, description='JSON data expected')

        data = request.json
        if not isinstance(data, dict):
            abort(400)

        self.set_object(*args, **kwargs)
        self.check_authorization()

        for key, value in data.items():
            setattr(self.obj, key, value)

        try:
            self.obj.save()
        except Exception:
            abort(500)

        output = self.get_content(*args, **kwargs)
        return jsonify(output)


class ListView(GenericView):
    methods = ['GET']
    action = 'list'

    def set_object(self, *args, **kwargs):
        try:
            namespace = current_identity.namespace
        except AttributeError:
            namespace = None
        self.obj = list(self.get_class().list(namespace, return_objects=True).values())

    def get_content(self, *args, **kwargs):
        return self.obj


class CreateView(GenericView):
    methods = ['POST']
    action = 'create'

    def save_object(self):
        self.obj.save()

    def after_save(self):
        pass

    def set_object(self, *args, **kwargs):
        cls = self.get_class()
        try:
            namespace = current_identity.namespace
        except AttributeError:
            namespace = None

        self.obj = cls(namespace, **request.json)

    def get_content(self, *args, **kwargs):
        return self.obj.get_dict(expand=True)

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        if not request.json:
            abort(400, description='JSON data expected')
        else:
            self.set_object(*args, **kwargs)
            self.check_authorization()
            try:
                self.save_object()
                self.after_save()
            except Exception as e:
                current_app.logger.error(e)
                abort(500, description='Creation failed with: {}'.format(e))

            output = self.get_content(*args, **kwargs)
            return jsonify(output)
