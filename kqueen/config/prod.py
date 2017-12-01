from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_LEVEL = 'INFO'

    KQUEEN_HOST = '0.0.0.0'

    # App secret
    SECRET_KEY = 'secret'

    # Jenkins engine settings
    JENKINS_API_URL = 'https://ci.mcp.mirantis.net'
    JENKINS_PROVISION_JOB_NAME = 'deploy-aws-k8s_ha_calico_sm'
    JENKINS_PROVISION_JOB_CTX = {}
    JENKINS_ANCHOR_PARAMETER = 'STACK_NAME'
    JENKINS_USERNAME = None
    JENKINS_PASSWORD = None
