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

    # Azure Container Service
    AKS_CLIENT_ID = '9ce5569a-8207-4bwe-b2a7-fba6da19a162'
    AKS_SECRET = '24dee47b-451f-b8c2-aae2-8c22b5ce353a'
    AKS_TENANT = '9be2469a-4466-451f-b8c2-3c1156f933a5'
    AKS_SUBSCRIPTION_ID = 'b0f2aac6-a64a-45df-89ec-3c1156f933a5'
