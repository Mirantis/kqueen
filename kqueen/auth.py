"""Authentication methods for API."""

from kqueen.models import Organization, User
from werkzeug.security import safe_str_cmp

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
    users = list(User.list(None, return_objects=True).values())
    username_table = {u.username: u for u in users}
    user = username_table.get(username)
    if user and user.active and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
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
    USER = user['id']
    ORGANIZATION = user['organization'].id
    ROLE = user['role']
    if resource:
        if hasattr(resource, 'owner'):
            OWNER = resource.owner.id
            OWNER_ORGANIZATION = resource.owner.organization.id
        elif isinstance(resource, User):
            OWNER = resource.id
            OWNER_ORGANIZATION = resource.organization.id
        elif isinstance(resource, Organization):
            OWNER_ORGANIZATION = resource.id

    # replace shorthands with full condition in policy_value
    shorthands = {
        'IS_ADMIN': 'ORGANIZATION == OWNER_ORGANIZATION and ROLE == "admin"',
        'IS_SUPERADMIN': 'ROLE == "superadmin"',
        'IS_OWNER': 'ORGANIZATION == OWNER_ORGANIZATION and USER == OWNER',
        'ADMIN_OR_OWNER': 'ORGANIZATION == OWNER_ORGANIZATION and (ROLE == "admin" or USER == OWNER)',
        'ALL': 'ORGANIZATION == OWNER_ORGANIZATION'
    }
    for short, full in shorthands.items():
        policy_value = policy_value.replace(short, full)

    if ROLE == 'superadmin':
        # no point in checking anything here
        return True

    try:
        authorized = eval(policy_value)
        if not isinstance(authorized, bool):
            logger.error('Policy evaluation did not return boolean: {}'.format(str(authorized)))
            authorized = False
    except Exception as e:
        logger.error('Policy evaluation failed: {}'.format(repr(e)))
        authorized = False
    return authorized
