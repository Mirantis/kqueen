from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = True
    LOG_LEVE = 'DEBUG'

    # App secret
    SECRET_KEY = 'secret'

    # Etcd settings
    ETCD_PREFIX = '/kqueen_test'

    # Jenkins engine settings
    JENKINS_API_URL = 'http://localhost'
    JENKINS_PROVISION_JOB_NAME = 'job_name'
    JENKINS_PROVISION_JOB_CTX = {}
    JENKINS_ANCHOR_PARAMETER = 'STACK_NAME'
    JENKINS_USERNAME = None
    JENKINS_PASSWORD = None
