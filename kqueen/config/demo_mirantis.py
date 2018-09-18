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

    # Enabled AUTH modules
    AUTH_MODULES = 'local,ldap'

    # Ldap config
    LDAP_URI = 'ldap://127.0.0.1'
    # Creds for Kqueen Read-only user
    LDAP_DN = 'cn=admin,dc=example,dc=org'
    LDAP_PASSWORD = 'heslo123'

    # Images for Kubespray (available images that can be provided are listed in the link below)
    # https://github.com/kubernetes-incubator/kubespray/blob/master/roles/download/defaults/main.yml
    HYPERKUBE_IMAGE_REPO = 'docker-prod-local.docker.mirantis.net/mirantis/kubernetes/hyperkube-amd64'
    HYPERKUBE_IMAGE_TAG = 'v1.9.8-4'
    CALICO_CNI_IMAGE_REPO = 'docker-prod-local.docker.mirantis.net/mirantis/projectcalico/calico/cni'
    CALICO_CNI_IMAGE_TAG = 'v1.11.6'
    CALICOCTL_IMAGE_REPO = 'docker-prod-local.docker.mirantis.net/mirantis/projectcalico/calico/ctl'
    CALICOCTL_IMAGE_TAG = 'v1.6.4'
    CALICO_NODE_IMAGE_REPO = 'docker-prod-local.docker.mirantis.net/mirantis/projectcalico/calico/node'
    CALICO_NODE_IMAGE_TAG = 'v2.6.10'
    POD_INFRA_IMAGE_REPO = 'docker-prod-local.docker.mirantis.net/mirantis/kubernetes/pause-amd64'
    POD_INFRA_IMAGE_TAG = 'v1.10.4-4'

    KS_DEFAULT_NAMESERVERS = "172.18.176.6"
    KS_NO_PROXY = "127.0.0.1,localhost,docker-prod-local.docker.mirantis.net,172.16.48.254," \
                  "cloud-cz.bud.mirantis.net,172.17.45.80"
    KS_OS_BLOCKSTORAGE_VERSION = "v2"
    KS_DOCKER_BIP = "10.13.0.1/16"
