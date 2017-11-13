from datetime import timedelta


class BaseConfig:
    DEBUG = False
    LOG_LEVEL = 'WARNING'

    KQUEEN_HOST = '127.0.0.1'
    KQUEEN_PORT = 5000

    # Babel default settings
    BABEL_DEFAULT_TIMEZONE = 'UTC'
    BABEL_DEFAULT_LOCALE = 'en'

    # etcd settings
    # ETCD_HOST
    # ETCD_PORT

    # JWT auth options
    JWT_DEFAULT_REALM = 'Login Required'
    JWT_AUTH_URL_RULE = '/api/v1/auth'
    JWT_EXPIRATION_DELTA = timedelta(hours=1)
    JWT_AUTH_HEADER_PREFIX = 'Bearer'

    # Cluster statuses
    CLUSTER_ERROR_STATE = 'Error'
    CLUSTER_OK_STATE = 'OK'
    CLUSTER_PROVISIONING_STATE = 'Deploying'
    CLUSTER_DEPROVISIONING_STATE = 'Destroying'
    CLUSTER_UNKNOWN_STATE = 'Unknown'

    # Provisioner statuses
    PROVISIONER_ERROR_STATE = 'Error'
    PROVISIONER_OK_STATE = 'OK'
    PROVISIONER_UNKNOWN_STATE = 'Not Reachable'

    @classmethod
    def get(cls, name, default=None):
        """Emulate get method from dict"""

        if hasattr(cls, name):
            return getattr(cls, name)
        else:
            return default

    @classmethod
    def to_dict(cls):
        """Return dict of all uppercase attributes"""

        out = {}

        for att_name in dir(cls):
            if att_name.isupper():
                out[att_name] = getattr(cls, att_name)

        return out
