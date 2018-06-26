from flask import abort
from flask import current_app
from flask import jsonify
from flask import request
from flask.views import View
from flask_jwt import _jwt_required, current_identity, JWTError
from kqueen.auth import is_authorized
from kqueen.models import Organization
from .helpers import get_object

import logging

logger = logging.getLogger('kqueen_api')


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
        # get user data
        if current_identity:
            user = current_identity.get_dict()
        else:
            return False

        policy_value = self.get_policy_value()
        if not policy_value:
            return False

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

    def get_policy_key(self):
        # get view class
        try:
            _class = self.get_class()
        except NotImplementedError:
            return ''

        return '{}:{}'.format(_class.__name__.lower(), self.action)

    def get_policy_value(self):
        # get policy_key
        policy_key = self.get_policy_key()
        if not policy_key:
            return ''

        policies = current_app.config.get('DEFAULT_POLICIES', {})

        # update them with organization level overrides
        organization = current_identity.organization
        if hasattr(organization, 'policy') and organization.policy:
            policies.update(organization.policy)

        try:
            policy_value = policies[policy_key]
        except KeyError:
            current_app.logger.error('Unknown policy {}'.format(policy_key))
            policy_value = ''
        return policy_value

    def set_object(self, *args, **kwargs):
        self.obj = get_object(self.get_class(), kwargs['pk'], current_identity)

        # check authorization for given object
        self.check_authorization()

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)
        output = self.get_content(*args, **kwargs)

        return jsonify(output)

    def hide_secure_data(self, obj):
        """Search and hide non-kqueen secure parameters
        """
        def nested_concealment(d):
            if not isinstance(d, dict):
                return
            for k, v in d.items():
                if isinstance(v, dict):
                    nested_concealment(v)
                if k in secure_keys:
                    d[k] = '*******'

        secure_keys = ['ssh_key', 'private_key', 'secret', 'subscription_id', 'password']

        nested_concealment(getattr(obj, 'metadata', None))
        nested_concealment(getattr(obj, 'parameters', None))
        return obj


class GetView(GenericView):
    methods = ['GET']
    action = 'get'

    def get_content(self, *args, **kwargs):
        self.obj = self.hide_secure_data(self.obj)
        return self.obj


class DeleteView(GenericView):
    methods = ['DELETE']
    action = 'delete'

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        self.set_object(*args, **kwargs)

        try:
            self.obj.delete()
        except Exception as e:
            abort(500, "Failed to delete object: {}".format(repr(e)))

        return jsonify({'id': self.obj.id, 'state': 'deleted'})


class UpdateView(GenericView):
    methods = ['PATCH']
    action = 'update'

    def get_content(self, *args, **kwargs):
        self.obj = self.hide_secure_data(self.obj)
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
    limit = 0
    offset = 0
    _objects_total = 0

    def _save_objects_range(self, objects):
        self._objects_total = len(objects)
        sorted_by_date = sorted(objects, key=lambda x: x.created_at, reverse=True)
        if self.limit > 0:
            self.obj = sorted_by_date[self.offset:self.offset + self.limit]
        else:
            self.obj = sorted_by_date

    def set_object(self, *args, **kwargs):
        self.offset = int(request.args.get('offset', -1))
        if self.offset != -1:
            self.limit = int(request.args.get('limit', 20))
        obj_class = self.get_class()

        def get_objects_list(namespace):
            return list(obj_class.list(namespace, return_objects=True).values())

        if request.args.get('all_namespaces'):
            objects = []
            for namespace in self.get_namespaces():
                objects += get_objects_list(namespace)
            self._save_objects_range(objects)
            self.check_authorization()
            return

        try:
            namespace = request.args.get('namespace') or current_identity.namespace
        except AttributeError:
            namespace = None

        self._save_objects_range(get_objects_list(namespace))
        self.check_authorization()

    def get_content(self, *args, **kwargs):
        if request.args.get('all_namespaces'):
            objs = []
            for obj in self.obj:
                namespace = obj._object_namespace
                obj_dict = obj.get_dict(expand=True)
                obj_dict['_namespace'] = namespace
                obj_dict = self.hide_secure_data(obj_dict)
                objs.append(obj_dict)
            return objs
        for i, obj in enumerate(self.obj):
            self.obj[i] = self.hide_secure_data(obj)
        return self.obj

    def dispatch_request(self, *args, **kwargs):
        self.check_authentication()
        try:
            self.set_object(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            abort(500, description='Unable to get objects list. {}'.format(repr(e)))
        output = self.get_content(*args, **kwargs)
        if self.limit > 0:
            return jsonify({'items': output, 'total': self._objects_total})
        return jsonify(output)


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
        self.obj = self.hide_secure_data(self.obj)
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
                current_app.logger.exception(e)
                abort(500, description='Creation failed with: {}'.format(e))

            output = self.get_content(*args, **kwargs)
            return jsonify(output)
