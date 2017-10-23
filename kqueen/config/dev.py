from datetime import timedelta


DEBUG = True

# JWT auth options
JWT_DEFAULT_REALM = 'Login Required'
JWT_AUTH_URL_RULE = '/api/v1/auth'
JWT_EXPIRATION_DELTA = timedelta(hours=1)

# App secret
SECRET_KEY = 'secret'

# Cluster statuses
CLUSTER_ERROR_STATE = 'Error'
CLUSTER_OK_STATE = 'OK'
CLUSTER_PROVISIONING_STATE = 'Deploying'
CLUSTER_DEPROVISIONING_STATE = 'Destroying'
CLUSTER_UNKNOWN_STATE = 'Unknown'

# Provisioner statuses
PROVISIONER_ERROR_STATE = 'Error'
PROVISIONER_OK_STATE = 'OK'
PROVISIONER_UNKNOWN_STATE = 'Not Reachable'

# Jenkins engine settings
JENKINS_API_URL = 'https://ci.mcp.mirantis.net'
JENKINS_PROVISION_JOB_NAME = 'deploy-aws-k8s_ha_calico_sm'
JENKINS_PROVISION_JOB_CTX = {}
JENKINS_ANCHOR_PARAMETER = 'STACK_NAME'
JENKINS_USERNAME = None
JENKINS_PASSWORD = None
