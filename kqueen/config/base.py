from datetime import timedelta


class BaseConfig:
    DEBUG = False

    # etcd settings
    # ETCD_HOST
    # ETCD_PORT

    # JWT auth options
    JWT_DEFAULT_REALM = 'Login Required'
    JWT_AUTH_URL_RULE = '/api/v1/auth'
    JWT_EXPIRATION_DELTA = timedelta(hours=1)

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
