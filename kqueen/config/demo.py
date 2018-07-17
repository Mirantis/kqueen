from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_CONFIG = 'kqueen/utils/logger_config.yml'

    KQUEEN_HOST = '0.0.0.0'

    # App secret - set this to random string >= 16 chars
    # SECRET_KEY = 'secret'

    # Set up this to enable Jenkins provisioner:
    JENKINS_API_URL = ''
    JENKINS_PROVISION_JOB_NAME = ''
    JENKINS_PROVISION_JOB_CTX = {}
    JENKINS_DEPROVISION_JOB_NAME = 'deploy-stack-cleanup'
    JENKINS_DEPROVISION_JOB_CTX = {
        'STACK_TYPE': 'aws'
    }
    JENKINS_PARAMETER_MAP = {
        'cluster_name': 'STACK_NAME',
        'cluster_uuid': 'KQUEEN_BUILD_ID'
    }
    JENKINS_USERNAME = None
    JENKINS_PASSWORD = None

    # Enabled AUTH modules
    AUTH_MODULES = 'local,ldap'

    # Ldap config
    LDAP_URI = 'ldap://127.0.0.1'
    # Creds for Kqueen Read-only user
    LDAP_DN = 'cn=admin,dc=example,dc=org'
    LDAP_PASSWORD = 'heslo123'
