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

    # SSH public key
    SSH_KEY = 'ssh-rsa AAAAB3NzadfadfafQEAylDZDzgMuEsJQpwFHDW+QivCVhryxXd1/HWqq1TVhJmT9oNAYdhUBnf/9kVtgmP0EWpDJtGSEaSugCmx8KE76I64RhpOTlm7wO0FFUVnzhFtTPx38WHfMjMdk1HF8twZU4svi72Xbg1KyBimwvaxTTd4zxq8Mskp3uwtkqPcQJDSQaZYv+wtuB6m6vHBCOTZwAognDGEvvCg0dgTU4hch1zoHSaxedS1UFHjUAM598iuI3+hMos/5hjG/vuay4cPLBJX5x1YF6blbFALwrQw8ZmTPaimqDUA9WD6KSmS1qg4rOkk4cszIfJ5vyymMrG+G3qk5LeT4VrgIgWQTAHyXw=='
