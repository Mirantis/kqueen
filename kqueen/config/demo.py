from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_CONFIG = 'kqueen/utils/logger_config.yml'

    KQUEEN_HOST = '0.0.0.0'

    # App secret - set this to random string >= 16 chars
    # SECRET_KEY = 'secret'

    # Jenkins engine settings
    JENKINS_API_URL = 'https://ci.mcp.mirantis.net'
    JENKINS_PROVISION_JOB_NAME = 'deploy_aws_k8s_kqueen_job'
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
