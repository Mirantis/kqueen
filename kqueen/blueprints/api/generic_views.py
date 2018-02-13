from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask.views import View
from flask_jwt import _jwt_required, current_identity, JWTError
from kqueen.auth import is_authorized
from kqueen.models import Organization
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

    def get_namespaces(self, *args, **kwargs):
        try:
            organizations = Organization.list(None).values()
        except Exception:
            organizations = []
        return [o.namespace for o in organizations]

    def check_authentication(self):
        _jwt_required(current_app.config['JWT_DEFAULT_REALM'])

    def check_authorization(self):
        # get view class
        try:
            _class = self.get_class()
        except NotImplementedError:
            return False

        # get user data
        if current_identity:
            user = current_identity.get_dict()
            organization = current_identity.organization
        else:
            return False

        # form policy key
        policy = '{}:{}'.format(_class.__name__.lower(), self.action)
        # get policies and update them with organization level overrides
        policies = current_app.config.get('DEFAULT_POLICIES', {})
        if hasattr(organization, 'policy') and organization.policy:
            policies.update(organization.policy)

        try:
            policy_value = policies[policy]
        except KeyError:
            current_app.logger.error('Unknown policy {}'.format(policy))
            return False

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
        else:
            if not is_authorized(user, policy_value, resource=self.obj):
                raise JWTError('Insufficient permissions',
                               'Your user account is lacking the necessary '
                               'permissions to perform this operation')

    def set_object(self, *args, **kwargs):
        self.obj = get_object(self.get_class(), kwargs['pk'], current_identity)

        # check authorization for given object
        self.check_authorization()

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)
        output = self.get_content(*args, **kwargs)

        return jsonify(output)


class GetView(GenericView):
    methods = ['GET']
    action = 'get'

    def get_content(self, *args, **kwargs):
        return self.obj


class DeleteView(GenericView):
    methods = ['DELETE']
    action = 'delete'

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)

        try:
            self.obj.delete()
        except Exception:
            abort(500)

        return jsonify({'id': self.obj.id, 'state': 'deleted'})


class UpdateView(GenericView):
    methods = ['PATCH']
    action = 'update'

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
        if request.args.get('all_namespaces'):
            objects = []
            for namespace in self.get_namespaces():
                objects = objects + list(self.get_class().list(namespace, return_objects=True).values())
            self.obj = objects
            self.check_authorization()
            return

        try:
            if request.args.get('namespace'):
                namespace = request.args.get('namespace')
            else:
                namespace = current_identity.namespace
        except AttributeError:
            namespace = None

        self.obj = list(self.get_class().list(namespace, return_objects=True).values())
        self.check_authorization()

    def get_content(self, *args, **kwargs):
        if request.args.get('all_namespaces'):
            objs = []
            for obj in self.obj:
                namespace = obj._object_namespace
                obj_dict = obj.get_dict(expand=True)
                obj_dict['_namespace'] = namespace
                objs.append(obj_dict)
            return objs
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

        self.obj = cls.create(namespace, **request.json)
        self.check_authorization()

    def get_content(self, *args, **kwargs):
        return self.obj.get_dict(expand=True)

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()

        if not request.json:
            abort(400, description='JSON data expected')
        else:
            self.set_object(*args, **kwargs)
            try:
                self.save_object()
                self.after_save()
            except Exception as e:
                current_app.logger.error(e)
                abort(500, description='Creation failed with: {}'.format(e))

            output = self.get_content(*args, **kwargs)
            return jsonify(output)
