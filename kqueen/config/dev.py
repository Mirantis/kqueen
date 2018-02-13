from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    LOG_PATH = 'log/kqueen'
    LOG_FILE = 'kqueen.log'

    # App secret
    SECRET_KEY = 'SecretSecretSecret123'

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
