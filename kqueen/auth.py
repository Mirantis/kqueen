from kqueen.models import User
from werkzeug.security import safe_str_cmp


def authenticate(username, password):
    users = list(User.list(return_objects=True).values())
    username_table = {u.username: u for u in users}
    user = username_table.get(username, None)
    if user and safe_str_cmp(user.password.encode('utf-8'), password.encode('utf-8')):
        return user


def identity(payload):
    user_id = payload['identity']
    try:
        user = User.load(user_id)
    except:
        user = None
    return user
