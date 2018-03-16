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

Sample configuration files are located in the `config/` directory. The default configuration file is `config/dev.py`.
To define a different configuration file set `KQUEEN_CONFIG_FILE` environment variable.  To override the values defined
in the configuration file, set the environment variable matching the KQUEEN_<config_parameter_name> pattern.

.. list-table:: Configuration options
    :header-rows: 1


    * - Name
      - Default
      - Description

    * - CONFIG_FILE
      - config/dev.py
      - Configuration file to load during startup

    * - DEBUG
      - False
      - Setting up debug mode for flask and all loggers

    * - SECRET_KEY
      - None
      - This key is used for server-side encryption (cookies, secret database fields) and must be at least 16 characters in length.
    * - ETCD_HOST
      - localhost
      - Hostname address of the etcd server
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
      - Optional. The default Jenkins password. Gets overridden if another value is specified in the request.
    * - JENKINS_PROVISION_JOB_CTX
      - {}
      - Dictionary for predefined Jenkins job context
    * - JENKINS_PROVISION_JOB_NAME
      - deploy-aws-k8s_ha_calico_sm
      - Name of the Jenkins job used to deploy a cluster.
    * - JENKINS_USERNAME
      - None
      - Optional. The default Jenkins username. Gets overridden if another value is specified in the request.

    * - CLUSTER_ERROR_STATE
      - Error
      - Caption for a cluster in error state.
    * - CLUSTER_OK_STATE
      - OK
      - Caption for a cluster in OK state.
    * - CLUSTER_PROVISIONING_STATE
      - Deploying
      - Caption for a cluster in provisioning state.
    * - CLUSTER_DEPROVISIONING_STATE
      - Destroying
      - Caption for a cluster in deprovisioning (deleting) state.
    * - CLUSTER_UNKNOWN_STATE
      - Unknown
      - Caption for a cluster with unknown state.

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
    * - PROVISIONER_ENGINE_WHITELIST
      - None
      - Enable only engines in list.

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
