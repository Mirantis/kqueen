"""Authentication methods for API."""

from kqueen.config import current_config
from kqueen.config.auth import AuthModules
from kqueen.models import Organization
from kqueen.models import User
from uuid import uuid4

import bcrypt
import importlib
import logging

logger = logging.getLogger('kqueen_api')


def generate_auth_options(auth_list):
    auth_options = {}

    methods = auth_list.split(',').strip()
    modules = AuthModules()
    for m in methods:
        if hasattr(modules, m):
            auth_options[m] = getattr(modules, m)

    if not auth_options:
        auth_options['local'] = {'engine': 'LocalAuth', 'param': {}}

    logger.debug('Auth config generated {}'.format(auth_options))
    return auth_options


def get_auth_instance(name):
    # Default type is local auth

    config = current_config()
    auth_config = generate_auth_options(config.get("AUTH_MODULES")).get(name, {})

    # If user auth is not specified clearly, use local
    if name == 'local' or name is None:
        auth_config = {'engine': 'LocalAuth', 'param': {}}

    module = importlib.import_module('kqueen.auth')
    auth_engine = auth_config.get('engine')
    logger.debug("Using {} Authentication Engine".format(auth_engine))

    if not auth_engine:
        raise Exception('Authentication type is set to {}, but engine class name is not found. '
                        'Please, set it with the "engine" key'.format(name))
    auth_class = getattr(module, auth_engine)

    if callable(auth_class):
        return auth_class(**auth_config.get('param', {}))


def authenticate(username, password):
    """
    Authenticate user.

    Args:
        username (str): Username to login
        password (str): Password

    Returns:
        user: authenticated user

    """

    # find user by username
    users = list(User.list(None, return_objects=True).values())
    username_table = {u.username: u for u in users}
    user = username_table.get(username)

    if user:
        given_password = password.encode('utf-8')

        logger.debug("User {} will be authenticated using {}".format(username, user.auth))

        auth_instance = get_auth_instance(user.auth)

        try:
            verified_user, verification_error = auth_instance.verify(user, given_password)
        except Exception as e:
            logger.exception("Verification method {} failed".format(user.auth))
            verified_user, verification_error = None, str(e)

        if isinstance(verified_user, User) and verified_user.active:
            logger.info("User {user} passed {method} auth successfully".format(user=user, method=user.auth))
            return verified_user
        else:
            logger.info("User {user} failed auth using {method} auth method with error {error}".format(
                user=user,
                method=user.auth,
                error=verification_error,
            ))


def identity(payload):
    """
    Read user_id from payload and return User.

    Args:
        payload (dict): Request payload

    Returns:
        user: detected user

    """
    user_id = payload['identity']
    try:
        user = User.load(None, user_id)
    except Exception:
        user = None
    return user


def encrypt_password(_password):
    config = current_config()
    rounds = config.get('BCRYPT_ROUNDS', 12)
    password = str(_password).encode('utf-8')
    encrypted = bcrypt.hashpw(password, bcrypt.gensalt(rounds)).decode('utf-8')
    return encrypted


def is_authorized(_user, policy_value, resource=None):
    """
    Evaluate if given user fulfills requirements of the given
    policy_value.

    Example:
        >>> user.get_dict()
        >>> {'username': 'jsmith', ..., 'role': 'member'}
        >>> is_authorized(user, "ALL")
        True
        >>> is_authorized(user, "IS_ADMIN")
        False

    Args:
        user (dict or User): User data
        policy_value (string or list): Condition written using shorthands and magic keywords

    Returns:
        bool: authorized or not
    """
    if isinstance(_user, User):
        user = _user.get_dict()
    elif isinstance(_user, dict):
        user = _user
    else:
        raise TypeError('Invalid type for argument user {}'.format(type(_user)))

    # magic keywords
    USER = user['id']                       # noqa: F841
    ORGANIZATION = user['organization'].id  # noqa: F841
    ROLE = user['role']
    if resource:
        validation, _ = resource.validate()
        if not validation:
            invalid = True

            # test if we are validating on create view and if so, patch missing object id
            if not resource.id:
                resource.id = uuid4()
                validation, _ = resource.validate()
                if validation:
                    invalid = False
                resource.id = None

            # if invalid resource is passed, let's just continue dispatch_request
            # so it can properly fail with 500 response code
            if invalid:
                logger.error('Cannot evaluate policy for invalid object: {}'.format(str(resource.get_dict())))
                return True

        # TODO: check owner has id and, organization ...
        if hasattr(resource, 'owner'):
            OWNER = resource.owner.id                            # noqa: F841
            OWNER_ORGANIZATION = resource.owner.organization.id  # noqa: F841
        elif isinstance(resource, User):
            OWNER = resource.id                                  # noqa: F841
            OWNER_ORGANIZATION = resource.organization.id        # noqa: F841
        elif isinstance(resource, Organization):
            OWNER_ORGANIZATION = resource.id                     # noqa: F841

    # predefined conditions for evaluation
    conditions = {
        'IS_ADMIN': 'ORGANIZATION == OWNER_ORGANIZATION and ROLE == "admin"',
        'IS_SUPERADMIN': 'ROLE == "superadmin"',
        'IS_OWNER': 'ORGANIZATION == OWNER_ORGANIZATION and USER == OWNER',
        'ADMIN_OR_OWNER': 'ORGANIZATION == OWNER_ORGANIZATION and (ROLE == "admin" or USER == OWNER)',
        'ALL': 'ORGANIZATION == OWNER_ORGANIZATION'
    }

    try:
        condition = conditions[policy_value]
    except KeyError:
        logger.exception('Policy evaluation failed. Invalid rule: {}'.format(str(policy_value)))
        return False

    if ROLE == 'superadmin':
        # no point in checking anything here
        logger.debug('User {} id {} authorized as {}'.format(user['username'], user['id'], user['role']))
        return True

    try:
        authorized = eval(condition)
        if not isinstance(authorized, bool):
            logger.error('Policy evaluation did not return boolean: {}'.format(str(authorized)))
            authorized = False
    except Exception as e:
        logger.exception('Policy evaluation failed: ')
        authorized = False
    logger.debug('User {} id {} authorized as {}'.format(user['username'], user['id'], user['role']))
    return authorized
