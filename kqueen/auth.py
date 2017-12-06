"""Authentication methods for API."""

from kqueen.models import User
from werkzeug.security import safe_str_cmp

import six


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


def is_authorized(user, policy_value):
    """
    Evaluate if given user fulfills requirements of the given
    policy_value.

    Example:
        >>> user.get_dict()
        >>> {'username': 'jsmith', ..., 'role': 'member'}
        >>> is_authorized(user, "all")
        True
        >>> is_authorized(user, ['admin'])
        False

    Args:
        user (dict or User): User data
        policy_value (string or list): Either "all" or list of allowed roles

    Returns:
        bool: authorized or not
    """
    if isinstance(user, User):
        role = user.get_dict()['role']
    elif isinstance(user, dict):
        role = user['role']
    else:
        raise TypeError('Invalid type for argument user {}'.format(type(user)))

    if role == 'superadmin':
        # no point in checking anything here
        return True
    if isinstance(policy_value, six.string_types) and policy_value == 'all':
        return True
    elif isinstance(policy_value, list) and role in policy_value:
        return True
    return False
