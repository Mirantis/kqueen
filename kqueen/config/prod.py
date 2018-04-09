from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_CONFIG = 'kqueen/utils/logger_config.yml'

    KQUEEN_HOST = '0.0.0.0'

    # Enabled AUTH modules
    AUTH_MODULES = 'local,ldap'

    # Ldap config
    LDAP_URI = 'ldap://127.0.0.1'
    # Creds for Kqueen Read-only user
    LDAP_DN = 'cn=admin,dc=example,dc=org'
    LDAP_PASSWORD = 'heslo123'
