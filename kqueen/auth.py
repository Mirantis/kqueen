"""Authentication methods for API."""

from kqueen.models import Organization, User
from uuid import uuid4

import logging

logger = logging.getLogger(__name__)


def authenticate(username, password):
    """
    Authenticate user.

    Args:
        username (str): Username to login
        password (str): Passwore

    Returns:
        user: authenticated user

    """
    from kqueen.server import bcrypt
    users = list(User.list(None, return_objects=True).values())
    username_table = {u.username: u for u in users}
    user = username_table.get(username)
    if user and user.active and bcrypt.check_password_hash(user.password, password):
        return user


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
        if not resource.validate():
            invalid = True
            # test if we are validating on create view and if so, patch missing object id
            if not resource.id:
                resource.id = uuid4()
                if resource.validate():
                    invalid = False
                resource.id = None
            # if invalid resource is passed, let's just continue dispatch_request
            # so it can properly fail with 500 response code
            if invalid:
                logger.error('Cannot evaluate policy for invalid object: {}'.format(str(resource.get_dict())))
                return True
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
        logger.error('Policy evaluation failed. Invalid rule: {}'.format(str(policy_value)))
        return False

    if ROLE == 'superadmin':
        # no point in checking anything here
        return True

    try:
        authorized = eval(condition)
        if not isinstance(authorized, bool):
            logger.error('Policy evaluation did not return boolean: {}'.format(str(authorized)))
            authorized = False
    except Exception as e:
        logger.error('Policy evaluation failed: {}'.format(repr(e)))
        authorized = False
    return authorized
