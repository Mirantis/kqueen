from datetime import timedelta

import json
import os


class BaseConfig:
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    LOG_CONFIG = 'kqueen/utils/logger_config.yml'

    KQUEEN_HOST = '127.0.0.1'
    KQUEEN_PORT = 5000

    # etcd settings
    # ETCD_HOST
    # ETCD_PORT

    # JWT auth options
    JWT_DEFAULT_REALM = 'Login Required'
    JWT_AUTH_URL_RULE = '/api/v1/auth'
    JWT_EXPIRATION_DELTA = timedelta(hours=1)
    JWT_AUTH_HEADER_PREFIX = 'Bearer'

    BCRYPT_ROUNDS = 12

    # Cluster statuses
    CLUSTER_ERROR_STATE = 'Error'
    CLUSTER_OK_STATE = 'OK'
    CLUSTER_PROVISIONING_STATE = 'Deploying'
    CLUSTER_DEPROVISIONING_STATE = 'Destroying'
    CLUSTER_RESIZING_STATE = 'Resizing'
    CLUSTER_UNKNOWN_STATE = 'Unknown'

    CLUSTER_STATE_ON_LIST = True

    # Provisioner statuses
    PROVISIONER_ERROR_STATE = 'Error'
    PROVISIONER_OK_STATE = 'OK'
    PROVISIONER_UNKNOWN_STATE = 'Not Reachable'

    PROVISIONER_ENGINE_WHITELIST = None
    PROVISIONER_STATE_ON_LIST = True

    # Timeout for cluster operations (in seconds)
    PROVISIONER_TIMEOUT = 3600
    PROMETHEUS_WHITELIST = '127.0.0.0/8'

    # Enabled AUTH modules
    AUTH_MODULES = 'local'

    # Auth config
    LDAP_URI = 'ldap://127.0.0.1'

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

    @classmethod
    def setup_policies(cls):
        """Read default policy file"""

        base_path = os.path.dirname(__file__)
        full_path = os.path.join(base_path, 'default_policy.json')
        fh = open(full_path, 'r')
        try:
            policy_string = fh.read()
            cls.DEFAULT_POLICIES = json.loads(policy_string)
        except Exception:
            cls.DEFAULT_POLICIES = {}
        finally:
            fh.close()
