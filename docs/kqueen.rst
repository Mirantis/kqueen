kqueen package
==============

.. toctree::
   :maxdepth: 3
   :caption: Contents:

   kqueen.engines

Models
-------

.. automodule:: kqueen.models
    :members:
    :undoc-members:
    :show-inheritance:


Kubernetes API
----------------------

.. automodule:: kqueen.kubeapi
    :members:
    :undoc-members:
    :show-inheritance:

Server
---------------------

.. automodule:: kqueen.server
    :members:
    :undoc-members:
    :show-inheritance:

Helpers
-----------------------

.. automodule:: kqueen.helpers
    :members:
    :undoc-members:
    :show-inheritance:

Serializers
--------------------------

.. automodule:: kqueen.serializers
    :members:
    :undoc-members:
    :show-inheritance:


Configuration
--------------

Example configuration files are located in `config/` directory. Default configuration file is `config/dev.py` and this can be configured by `KQUEEN_CONFIG_FILE` environment variable. Any environment variable matching name `KQUEEN_*` will be loaded and merged with configuration file.

.. list-table:: Configuration options
    :header-rows: 1


    * - Name
      - Default
      - Description

    * - CONFIG_FILE
      - config/dev.py
      - Configuration file to load during startup

    * - LOG_LEVEL
      - WARNING
      - Logging level for `app.logger` (string)

    * - SECRET_KEY
      - None
      - This key is used for server-side encryption (cookies, secret database fields).
    * - ETCD_HOST
      - localhost
      - Address of hostname for etcd server
    * - ETCD_PORT
      - 4001
      - Port for etcd server
    * - ETCD_PREFIX
      - /kqueen
      - Prefix URL for objects in etcd


    * - JWT_DEFAULT_REALM
      - Login Required
      -
    * - JWT_AUTH_URL_RULE
      - /api/v1/auth
      - Authentication endpoint returning token.
    * - JWT_EXPIRATION_DELTA
      - timedelta(hours=1)
      - JWT token lifetime.

    * - JENKINS_ANCHOR_PARAMETER
      - STACK_NAME
      - This parameter is used to match Jenkins builds with clusters.
    * - JENKINS_API_URL
      - None
      - REST API for Jenkins
    * - JENKINS_PASSWORD
      - None
      - Password for Jenkins login.
    * - JENKINS_PROVISION_JOB_CTX
      - {}
      -
    * - JENKINS_PROVISION_JOB_NAME
      - deploy-aws-k8s_ha_calico_sm
      - Name of Jenkins job used to deploy cluster.
    * - JENKINS_USERNAME
      - None
      - Username for Jenkins login.

    * - CLUSTER_ERROR_STATE
      - Error
      - Caption for cluster error state.
    * - CLUSTER_OK_STATE
      - OK
      - Caption for cluster OK state.
    * - CLUSTER_PROVISIONING_STATE
      - Deploying
      - Caption for cluster in provisioning state.
    * - CLUSTER_DEPROVISIONING_STATE
      - Destroying
      - Caption for cluster in deprovisioning (deleting) state.
    * - CLUSTER_UNKNOWN_STATE
      - Unknown
      - Caption for cluster with unknown state.

    * - CLUSTER_STATE_ON_LIST
      - True
      - Update state of clusters on cluster list. This can be may be disabled for organizations with large number of clusters in deploy state.

    * - PROVISIONER_ERROR_STATE
      - Error
      - Caption for errored provisioner.
    * - PROVISIONER_OK_STATE
      - OK
      - Caption for working provisioner.
    * - PROVISIONER_UNKNOWN_STATE
      - Not Reachable
      - Caption for unknown provisioner.

    * - PROMETHEUS_WHITELIST
      - 127.0.0.0/8
      - Addresses allowed to access metrics endpoint without token


Backup
-------

The only one statefull component of Kqueen is the etcd and users should follow https://coreos.com/etcd/docs/latest/v2/admin_guide.html#disaster-recovery. We are using `v2` etcd keys so example backup workflow can be:

::

  # Backup etcd to directory /root/backup/ (etcd data stored in /var/lib/etcd/default)
  etcdctl backup --data-dir /var/lib/etcd/default --backup-dir /root/backup/

Recovery

::

  # Move data to etcd directory
  mv -v /root/backup/* /var/lib/etcd/default/

  # Start new etcd with these two extra parameters (among the other)
  # for example: etcd --force-new-cluster


kqueen
