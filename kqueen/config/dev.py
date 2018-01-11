from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

    # App secret
    SECRET_KEY = 'SecretSecretSecret123'

    # Jenkins engine settings
    JENKINS_API_URL = 'https://ci.mcp.mirantis.net'
    JENKINS_PROVISION_JOB_NAME = 'deploy-aws-k8s_ha_calico_sm'
    JENKINS_PROVISION_JOB_CTX = {}
    JENKINS_ANCHOR_PARAMETER = 'STACK_NAME'
    JENKINS_USERNAME = None
    JENKINS_PASSWORD = None
