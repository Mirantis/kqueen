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

Sample configuration files are located in the ``config/`` directory. The default
configuration file is ``config/dev.py``.
To define a different configuration file, set the ``KQUEEN_CONFIG_FILE``
environment variable. To override the values defined in the configuration file,
set the environment variable matching the ``KQUEEN_<config_parameter_name>``
pattern.

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
      - Debug mode for flask and all loggers

    * - SECRET_KEY
      - None
      - This key is used for server-side encryption (cookies, secret database
        fields) and must be at least 16 characters in length.
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
      - The default realm
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
      - Optional. The default Jenkins password. It can be overridden by
        another value specified in the request.
    * - JENKINS_PROVISION_JOB_CTX
      - {}
      - Dictionary for predefined Jenkins job context
    * - JENKINS_PROVISION_JOB_NAME
      - deploy-aws-k8s_ha_calico_sm
      - Name of the Jenkins job used to deploy a cluster.
    * - JENKINS_USERNAME
      - None
      - Optional. The default Jenkins username. It can be overridden by
        another value specified in the request.

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
      - Update the state of clusters on cluster list. This can be disabled for
        organizations with a large number of clusters in the deploy state.

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
      - Enable only engines in the list.

    * - PROMETHEUS_WHITELIST
      - 127.0.0.0/8
      - Addresses allowed to access metrics endpoint without token


Default user access configuration
_________________________________

Default CRUD (Create, Read, Update, Delete) model for KQueen user roles.

Superadmin view
~~~~~~~~~~~~~~~

- ``CRUD`` all organizations.
- ``CRUD/Manage`` all members.
- ``CRUD/Manage`` all member roles.
- Full admin rights.

Admin view
~~~~~~~~~~

- Invite/remove members in own organization (Email/LDAP).
- ``CRD`` all provisioners.
- ``CRUD`` all clusters.
- Collect Prometheus metrics.
- Full user rights.


User view
~~~~~~~~~

- Login.
- ``R`` organization members.
- ``R`` provisioners.
- ``CRUD`` self clusters.


Before you provision a Kubernetes cluster, you may need to deploy and configure
the following external services:

* NGINX proxy server, to configure SSL support, domain naming, and to define
  certificates.

* Mail server, to enable members management. For example, to enable a user to
  invite other users by email. You can use the KQueen predefined mail service
  or run a new one.

* LDAP server, to enable members management through LDAP. For example, to
  enable a user to invite other users from defined LDAP server. You can use
  the KQueen predefined LDAP service or run a new one.

* Prometheus server, to extend the monitoring in KQueen. You can either use a
  predefined Prometheus server, defined in the ``docker-compose.production.yml``
  file or use an external one. For an external one, you must include the rules
  from ``kqueen/prod/prometheus`` to the existing Prometheus service.


Set up the NGINX server
-----------------------

#. Open the ``.env`` file for editing.
#. Configure the variables the Nginx section:

   .. code-block:: bash

      # Domain name for service. Should be equal with name in generated ssl-certificate
      NGINX_VHOSTNAME=demo.kqueen.net
      # Directory path for certificates in container.Finally it look like $NGINX_SSL_CERTIFICATE_DIR/$NGINX_VHOSTNAME
      NGINX_SSL_CERTIFICATE_DIR=/mnt/letsencrypt

#. Open the ``docker-compose.production.yml`` file for editing.
#. Verify the proxy service configuration. Pay attention to the following
   variables:

   #. ``VHOSTNAME``, the domain name for the KQueen service. This domain name
      must be the same as the domain name in the generated certificates. By
      default, ``NGINX_VHOSTNAME`` from the ``.env`` file is used.
   #. ``SSL_CERTIFICATE_DIR``, the mapped directory for certificates
      forwarding into a docker container. By default, the
      ``$NGINX_SSL_CERTIFICATE_DIR/$NGINX_VHOSTNAME`` variable from the
      ``.env`` file is used.
   #. ``SSL_CERTIFICATE_PATH``, the path for the cert+key certificate. The
      default is ``$SSL_CERTIFICATE_DIR/fullchain.cer``.
   #. ``SSL_CERTIFICATE_KEY_PATH``, the path for the certificate key. The
      default is ``$SSL_CERTIFICATE_DIR/$VHOSTNAME.key``.
   #. ``SSL_TRUSTED_CERTIFICATE_PATH``, the path for the certificate. The
      default is ``$SSL_CERTIFICATE_DIR/ca.cer``.

.. note::

   Verify that the local certificates have the same name as the ones defined
   in the variables.

#. Map the volumes with certificates. The destination path must be the same as
   ``SSL_CERTIFICATE_DIR``. For example:

   .. code-block:: yaml

      volumes:
        - /your/local/cert/storage/kqueen/certs/:${NGINX_SSL_CERTIFICATE_DIR}/${NGINX_VHOSTNAME}:ro

#. Build the proxy service image:

   .. code-block:: bash

      docker-compose -f docker-compose.production.yml build --no-cache

#. Rerun the production services:

   .. code-block:: bash

      docker-compose -f docker-compose.yml -f docker-compose.production.yml  up --force-recreate
 

Set up the mail server
----------------------

#. Open the ``docker-compose.production.yml`` file for editing.
#. Define the mail service. For example:

   .. code-block:: yaml

      mail:
        image: modularitycontainers/postfix
        volumes:
          - /var/spool/postfix:/var/spool/postfix
          - /var/mail:/var/spool/mail
        environment:
          MYHOSTNAME: 'mail'

#. Configure the following variables in the KQueen UI service section:

   .. code-block:: yaml

      KQUEENUI_MAIL_SERVER: mail
      KQUEENUI_MAIL_PORT: 10025


Once done, you should be able to invite members through email notifications.
The email will contain an activation link for the KQueen service with a
possibility to set a password. Users with superadmin rights can also manage
member roles.

.. note::

   Volume-mapping for mail containers is an additional feature that enables
   storing the mailing history and forwards an additional postfix mail
   configuration. You must properly configure it on the local machine.
   Otherwise, you can run the mail server without volume mapping.

Set up the LDAP server
----------------------

.. note::

   If you are using an external LDAP server, skip steps 1 and 2.

#. Open the ``docker-compose.auth.yml`` file for editing.
#. Define the LDAP service. For example:

   .. code-block:: yaml

      services:
        ldap:
          image: osixia/openldap
          command:
            - --loglevel
            - debug
          ports:
            - 127.0.0.1:389:389
            - 127.0.0.1:636:636
          environment:
            LDAP_ADMIN_PASSWORD: 'heslo123'
        phpldapadmin:
          image: osixia/phpldapadmin:latest
          container_name: phpldapadmin
          environment:
            PHPLDAPADMIN_LDAP_HOSTS: 'ldap'
            PHPLDAPADMIN_HTTPS: 'false'
          ports:
            - 127.0.0.1:8081:80
          depends_on:
            - ldap

#. Open the ``docker-compose.production.yml`` file for editing.
#. Configure the following variables in the KQueen UI service section:

   .. code-block:: yaml

      KQUEEN_LDAP_URI: 'ldap://ldap'
      KQUEEN_LDAP_DN: 'cn=admin,dc=example,dc=org'
      KQUEEN_LDAP_PASSWORD: 'secret'
      KQUEEN_AUTH_MODULES: 'local,ldap'
      KQUEENUI_LDAP_AUTH_NOTIFY: 'False'

   .. note::

      * ``KQUEEN_LDAP_DN`` and ``KQUEEN_LDAP_PASSWORD`` are user credentials
        with a read-only access for LDAP search.
      * ``KQUEEN_AUTH_MODULES`` is the list of enabled authentication methods.
      * Set ``KQUEENUI_LDAP_AUTH_NOTIFY`` to ``True`` to enable additional email
        notifications for LDAP users.
   
Once done, you should be able to invite members through LDAP. Define ``cn`` as
the username for a new member.

.. note::

   ``dc`` for invited users is predefined in ``KQUEEN_LDAP_DN``.

Users with superadmin rights can also manage member roles.

Set up metrics collecting
-------------------------

#. Open the ``docker-compose.production.yml`` file for editing.
#. Configure the Prometheus service IP address, port, and volumes. For example:

   .. code-block:: yaml

      prometheus:
        image: prom/prometheus
        restart: always
        ports:
          - 127.0.0.1:9090:9090
        volumes:
          - ./prod/prometheus/:/etc/prometheus/:Z
          - /mnt/storage/kqueen/prometheus/:/prometheus/
        links:
          - api
          - etcd

#. Define the Prometheus scraper IP address in the KQueen API service section:

   .. code-block:: yaml

      KQUEEN_PROMETHEUS_WHITELIST: '172.16.238.0/24'

The metrics can be obtained using the KQueen API or Prometheus API:

* Kqueen API:

  .. code-block:: bash

     TOKEN=$(curl -s -H "Content-Type: application/json" --data '{"username":"admin","password":"default"}' -X POST <<kqueen_api_host>>:5000/api/v1/auth | jq -r '.access_token'); echo $TOKEN
     curl -H "Authorization: Bearer $TOKEN" <<kqueen_api_host>>:5000/metrics/


* Prometheus API:

  #. Add the scraper IP address to the ``PROMETHEUS_WHITELIST`` configuration.
  #. Run the following command:

     .. code-block:: bash

        curl <<prometheus_host>>:<<prometheus_port>>/metrics

All application metrics are exported to the **/metrics**  API endpoint. Any
external Prometheus instance can then scrape this metric.


Provision a Kubernetes cluster
------------------------------

You can provision a Kubernetes cluster using various community of engines,
such as Google Kubernetes engine or Azure Kubernetes Service.

Provision a Kubernetes cluster using Google Kubernetes Engine
_____________________________________________________________

#. Log in to Google Kubernetes Engine (https://console.cloud.google.com).
#. Select your Project.
#. Navigate to ``API’s & Services``  -> ``Credentials`` tab and click
   ``Create credentials``.
#. From ``Service Account key``, select your service account.
#. Select ``JSON`` as the key format.
#. Download the JSON snippet.
#. Log in to the KQueen web UI.
#. From the ``Create Provisioner`` page, select ``Google Kubernetes Engine``.
#. Insert the downloaded JSON snippet that contains the service account key
   and submit the provisioner creation.
#. Click ``Deploy Cluster``.
#. Select the defined GCE provisioner.
#. Specify the cluster requirements.
#. Click ``Submit``.
#. To track the cluster status, navigate to the KQueen main dashboard.

Provision a Kubernetes cluster using Openstack Kubespray Engine
_______________________________________________________________

#. Log in to Openstack Horizon Dashboard.
#. Select your Project.
#. Navigate to Project`-> ``Compute`` -> ``Access & Security`` -> ``API Access`` tab and click
   ``Download OpenStack RC File``.
#. Log in to the KQueen web UI.
#. From the ``Create Provisioner`` page, select ``Openstack Kubespray Engine``.
#. Specify provisioner requirements with the Openstack RC File, downloaded earlier.
#. Click ``Deploy Cluster``.
#. Select the defined Openstack provisioner.
#. Specify the cluster requirements, and pay attention on the following cases:

   #. ``SSH key name`` is name of SSH key pair. You should choose from existing pairs or create a new one.
   #. ``Image name`` image must be one of the `Kubespray supported Linux distributions <https://github.com/kubernetes-incubator/kubespray#supported-linux-distributions>`_.
   #. ``Flavor`` must be at least ``m1.small`` (2GB RAM, dual-core CPU).
   #. ``SSH username`` is login username for nodes. It depends on the defined image.
   #. ``Comma separated list of nameservers`` check, that it contains required dns-servers to resolve Openstack url's (like authentication url).

#. Click ``Submit``.
#. To track the cluster status, navigate to the KQueen main dashboard.

.. note::

   The Openstack configuration should correspond to the `Kubespray deployment requirements <https://github.com/kubernetes-incubator/kubespray#requirements>`_.

.. note::

   Currently, the cluster can not be downscaled to lower nodes count than the count of master nodes.

.. note::

   Make sure the default security group allows VMs to connect with each other and access to the Internet (if current Node config does not contain full Kubespray requirements setup).

.. note::

   The following network `kube_pods_subnet: 10.233.64.0/18` must be unused in your network infrastructure.
   IP addresses will be assigned from this range to individual pods.


Provision a Kubernetes cluster using Azure Kubernetes Service
_____________________________________________________________

#. Log in to Azure Kubernetes Service (https://portal.azure.com).
#. Create an Azure Active Directory Application as described in the official
   Microsoft `Documentation <https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal#create-an-azure-active-directory-application>`_.
#. Copy the ``Application ID``, ``Application Secret``, ``Tenant ID``
   (Directory ID), and ``Subscription ID`` to use in step 8.
#. Set the ``Owner`` role to your Application in the Subscription settings to
   enable the creation of Kubernetes clusters.
#. Navigate to the ``Resource groups`` tab and create a resource group. Copy
   the ``Resource group name`` to use in step 8.
#. From the ``Resource groups`` -> ``your_group`` -> ``Access Control (IAM)``
   tab, verify that the Application has the ``Owner`` role in the resource
   group.
#. Log in to the KQueen web UI.
#. From the ``Create provisioner`` tab, select the AKS engine and set the
   following:

	#. Set the ``Client ID`` as Application ID from step 3.
	#. Set the ``Resource group name`` as Resource group name from step 5.
	#. Set the ``Secret`` as Application Secret from step 3.
	#. Set the ``Subscription ID`` as  Subscription ID from step 3.
	#. Set the ``Tenant ID`` as Tenant(Directory) ID from step 3.

#. In the KQueen web UI, click ``Deploy Cluster``.
#. Select the AKS provisioner.
#. Specify the cluster requirements.
#. Specify the public SSH key to connect to AKS VMs.

   .. note::

      For an SSH access to created VMs, assign a public IP address to a
      VM as described in
      `How to connect to Azure AKS Kubernetes node VM by SSH  
      <https://gist.github.com/naumvd95/576d6e48200597ca89b26de15e8d3675>`_.
      Once done, run the ``ssh azureuser@<<public_ip>> -i .ssh/your_defined_id_rsa``
      command.

#. Click ``Submit``.
#. To track the cluster status, navigate to the KQueen main dashboard.

.. note::

   The Admin Console in the Azure portal is supported only in Internet Explorer
   and Microsoft Edge and may fail to operate in other browsers due to
   Microsoft `issues <https://microsoftintune.uservoice.com/forums/291681-ideas/suggestions/18602776-admin-console-support-on-mac-osx>`_.

.. note::

   The AKS creates a separate resource during the creation of a Kubernetes
   cluster and uses the defined resource group as a prefix. This may affect
   your billing. For example:

   .. code-block:: text

      Your Resource Group : Kqueen
      Additional cluster-generated Resource Group: MC_Kqueen_44a37a65-1dff-4ef8-97ca-87fa3b8aee62_eastus

For more information, see `Issues <https://github.com/Azure/AKS/issues/3>`_,
and https://docs.microsoft.com/en-us/azure/aks/faq#why-are-two-resource-groups-created-with-aks.


Manually add an existing Kubernetes cluster to KQueen
_____________________________________________________

#. Log in to the KQueen web UI.
#. Click ``Create Provisioner``.
#. Enter the cluster name.
#. In the ``Engine`` drop-down list, select ``Manual Engine`` and click
   ``Submit``.
#. Click ``Deploy Cluster``.
#. Select the predefined manual provisioner and attach a valid Kubernetes
   configuration file.
#. Click ``Submit``.

The Kubernetes cluster will be attached in a read-only mode.


Backup and recover Etcd
-----------------------

Etcd is the only stateful component of KQueen. To recover etcd in case of a
failure, follow the procedure described in
`Disaster recovery <https://coreos.com/etcd/docs/latest/v2/admin_guide.html#disaster-recovery>`_.

.. note::

   The ``v2`` etcd keys are used for the deployment.

Example of the etcd backup workflow:

.. code-block:: bash

   # Backup etcd to directory /root/backup/ (etcd data stored in /var/lib/etcd/default)
   etcdctl backup --data-dir /var/lib/etcd/default --backup-dir /root/backup/


Example of the etcd recovery workflow:

.. code-block:: bash

   # Move data to etcd directory
   mv -v /root/backup/* /var/lib/etcd/default/

   # Start new etcd with these two extra parameters (among the other)
   # for example: etcd --force-new-cluster

.. include:: kqueen.cli_api_examples.rst

.. include:: kqueen.cli_gcloud_examples.rst

.. include:: kqueen.cli_azure_examples.rst

