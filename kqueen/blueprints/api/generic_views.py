from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask.views import View
from flask_jwt import _jwt_required, current_identity, JWTError
from kqueen.auth import is_authorized
from .helpers import get_object


class GenericView(View):
    def get_class(self):
        if hasattr(self, 'object_class'):
            return self.object_class
        else:
            raise NotImplementedError('Missing object_class variable or get_class')

    def get_content(self, *args, **kwargs):
        raise NotImplementedError

    def _policy_check(self):
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
        if policy_value and user:
            if not is_authorized(user, policy_value):
                raise JWTError('Insufficient permissions',
                               'Your user account is lacking the necessary '
                               'permissions to perform this operation')

    def check_access(self):
        _jwt_required(current_app.config['JWT_DEFAULT_REALM'])
        self._policy_check()

    def dispatch_request(self, *args, **kwargs):
        self.check_access()
        output = self.get_content(*args, **kwargs)

        return jsonify(output)


class GetView(GenericView):
    methods = ['GET']
    action = 'get'

    def get_content(self, *args, **kwargs):
        return get_object(self.get_class(), kwargs['pk'], current_identity)


class DeleteView(GenericView):
    methods = ['DELETE']
    action = 'delete'

    def dispatch_request(self, *args, **kwargs):
        self.check_access()

        obj = get_object(self.get_class(), kwargs['pk'], current_identity)

        try:
            obj.delete()
        except Exception:
            abort(500)

        return jsonify({'id': obj.id, 'state': 'deleted'})


class UpdateView(GenericView):
    methods = ['PATCH']
    action = 'update'

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
        except Exception:
            abort(500)

        return super(UpdateView, self).dispatch_request(*args, **kwargs)


class ListView(GenericView):
    methods = ['GET']
    action = 'list'

    def get_content(self, *args, **kwargs):
        try:
            namespace = current_identity.namespace
        except AttributeError:
            namespace = None

        return list(self.get_class().list(namespace, return_objects=True).values())


class CreateView(GenericView):
    methods = ['POST']
    action = 'create'

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
