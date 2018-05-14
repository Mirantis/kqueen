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
To define a different configuration file, set the `KQUEEN_CONFIG_FILE` environment variable.  To override the values defined
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
      - Debug mode for flask and all loggers

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
      - Optional. The default Jenkins password. It can be overridden by another value specified in the request.
    * - JENKINS_PROVISION_JOB_CTX
      - {}
      - Dictionary for predefined Jenkins job context
    * - JENKINS_PROVISION_JOB_NAME
      - deploy-aws-k8s_ha_calico_sm
      - Name of the Jenkins job used to deploy a cluster.
    * - JENKINS_USERNAME
      - None
      - Optional. The default Jenkins username. It can be overridden by another value specified in the request.

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
      - Update the state of clusters on cluster list. This can be disabled for organizations with a large number of clusters in the deploy state.

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

Before you provision a Kubernetes cluster, you may need to deploy and configure the following external services:

* NGINX proxy server, to configure SSL support, domain naming, and to define certificates.

* Mail server, to enable members management. For example, to enable a user to invite other users by email. You can use the KQueen predefined mail service or run a new one.

* LDAP server, to enable members management through LDAP. For example, to enable a user to invite other users from defined LDAP server. You can use the KQueen predefined LDAP service or run a new one.

* Prometheus server, to extend the monitoring in KQueen. You can either use a predefined Prometheus server, defined in the docker-compose.production.yml file or use an external one. For an external one, you must include the rules from kqueen/prod/prometheus to the existing Prometheus service.


To set up the NGINX server
---------------------------------

1. Open the '.env' file for editing.
2. Configure the variables the Nginx section:

   .. code-block:: bash

      # Domain name for service. Should be equal with name in generated ssl-certificate
      NGINX_VHOSTNAME=demo.kqueen.net
      # Directory path for certificates in container.Finally it look like $NGINX_SSL_CERTIFICATE_DIR/$NGINX_VHOSTNAME
      NGINX_SSL_CERTIFICATE_DIR=/mnt/letsencrypt

2. Open the docker-compose.production.yml file for editing.
3. Verify the proxy service configuration. Pay attention on following variables:

  1. ``VHOSTNAME``, the domain name for the KQueen service. Should be the same as the domain name in the generated certificates. By default, the ``NGINX_VHOSTNAME`` from the `.env` file is used. 
  2. ``SSL_CERTIFICATE_DIR``, the mapped directory for certificates forwarding into a docker container. By default, the ``$NGINX_SSL_CERTIFICATE_DIR/$NGINX_VHOSTNAME`` variable from the `.env` file is used. 
  3. ``SSL_CERTIFICATE_PATH``, the path for the cert+key certificate. The default is ``$SSL_CERTIFICATE_DIR/fullchain.cer``.
  4. ``SSL_CERTIFICATE_KEY_PATH``, the path for the certificate key. The default is ``$SSL_CERTIFICATE_DIR/$VHOSTNAME.key``.
  5. ``SSL_TRUSTED_CERTIFICATE_PATH``, the path for the certificate. The default is ``$SSL_CERTIFICATE_DIR/ca.cer``.

.. note::

   Verify that the local certificates have the same name as the ones defined in the variables.

4. Map the volumes with certificates. The destination path should be the same as ``SSL_CERTIFICATE_DIR``. Example:

   .. code-block:: yaml

      volumes:
        - /your/local/cert/storage/kqueen/certs/:${NGINX_SSL_CERTIFICATE_DIR}/${NGINX_VHOSTNAME}:ro

5. Build the proxy service image:

   .. code-block:: bash

      docker-compose -f docker-compose.production.yml build --no-cache

6. Re-run the production services:

   .. code-block:: bash

      docker-compose -f docker-compose.yml -f docker-compose.production.yml  up --force-recreate
 

To set up the mail server
--------------------------------

1. Open the docker-compose.production.yml file for editing.
2. Define the mail service. For example:

   .. code-block:: yaml

      mail:
        image: modularitycontainers/postfix
        volumes:
          - /var/spool/postfix:/var/spool/postfix
          - /var/mail:/var/spool/mail
        environment:
          MYHOSTNAME: 'mail'

3. Configure the following variables in the KQueen UI service section:

   .. code-block:: yaml

      KQUEENUI_MAIL_SERVER: mail
      KQUEENUI_MAIL_PORT: 10025


Once done, you should be able to invite members through email notifications. The email will contain an activation link for the KQueen service with a possibility to set a password. Users with
superadmin rights can also manage member roles.


.. note::

   Volume-mapping for mail containers is an additional feature that enables storing the mailing history and forwards an additional postfix mail configuration. You must properly configure it on the local machine. Otherwise, you can run the mail server without volume-mapping.

To set up the LDAP server
--------------------------------

1. Open the docker-compose.auth.yml file for editing.
2. Define the LDAP service. For example:

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

3. Open the docker-compose.production.yml file for editing.
4. Configure the following variables in the KQueen UI service section:

   .. code-block:: yaml

      KQUEEN_LDAP_URI: 'ldap://ldap'
      KQUEEN_LDAP_DN: 'cn=admin,dc=example,dc=org'
      KQUEEN_LDAP_PASSWORD: 'secret'
      KQUEEN_AUTH_MODULES: 'local,ldap'
      KQUEENUI_LDAP_AUTH_NOTIFY: 'False'


.. note::

   Set ``KQUEENUI_LDAP_AUTH_NOTIFY`` to ``True`` to enable additional email notifications for LDAP users.

.. note::

   ``KQUEEN_AUTH_MODULES`` is list with enabled Authentication methods.

.. note::

   ``KQUEEN_LDAP_DN``/ ``KQUEEN_LDAP_PASSWORD`` User credentials with read-only access for Ldap-search

.. note::

   In case of using external LDAP server, skip steps 1 and 2.

Once done, you should be able to invite members through LDAP. Define ``cn`` as username for new member:

.. note::

   'dc' for invited users equal to predefined in ``KQUEEN_LDAP_DN``

Users with superadmin rights can also manage member roles.

To set up metrics collecting
-----------------------------------

1. Open the docker-compose.production.yml file for editing.
2. Configure the Prometheus service IP address, port, and volumes. For example:

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
3.  Define the Prometheus scraper IP address in the KQueen API service section:

.. code-block:: yaml

   KQUEEN_PROMETHEUS_WHITELIST: '172.16.238.0/24'

The metrics can be obtained using the KQueen API or Prometheus API:

* Kqueen API:

.. code-block:: bash

   TOKEN=$(curl -s -H "Content-Type: application/json" --data '{"username":"admin","password":"default"}' -X POST <<kqueen_api_host>>:5000/api/v1/auth | jq -r '.access_token'); echo $TOKEN
   curl -H "Authorization: Bearer $TOKEN" <<kqueen_api_host>>:5000/metrics/


* Prometheus API:

   1. Add the scraper IP address to ``PROMETHEUS_WHITELIST`` configuration.
   2. Run the following command:

      .. code-block:: bash

         curl <<prometheus_host>>:<<prometheus_port>>/metrics


All application metrics are exported to the **/metrics**  API endpoint. Any external Prometheus instance can then scrape this metric.


Provision a Kubernetes cluster
------------------------------

You can provision a Kubernetes cluster using various community of engines, such as Google Kubernetes engine or Azure Kubernetes Service.

To provision a Kubernetes cluster using the Openstack Engine:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Login into your Openstack Horizon Dashboard
2. Switch to your Project/Tenant
3. Navigate to ``Project`` -> ``Compute`` -> ``API Access`` tab and click ``View Credentials``
4. Copy ``User Name``, ``Project Name``, ``Authentication URL``
5. Navigate to ``Project`` -> ``Network`` -> ``Networking``
6. Click on your Private Network, then click on a Subnet of your Private Network.
7. Copy the ID of the Subnet and the Network ID
8. Navigate to ``Project`` -> ``Network`` -> ``Networking``
9. Click on your Public Network, then copy the public network ID
10. Import into Glance the following image http://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud-1801-01.qcow2
11. Download the following heat template https://github.com/Mirantis/kqueen/prod/openstack/heat-templates/kubernetes.yaml
12. Under the ``parameters:`` section replace the private_net_id, private_subnet_id and public_net_id default values with ones you copied.
13. Login in to KQueen web UI.
14. From the ``Create Provisioner`` tab, select ``Openstack Engine``.
15. Fill the form with the User Name, Password, Project/Tenant Name and Authentication URL
16. Copy/Paste the modify kubernetes.yaml heat template under the field ``Heat template to use for building k8s clusters``
17. Save the provisioner
18. Click ``Deploy Cluster``.
19. Select the defined Openstack provisioner.
20. Specify the cluster requirements.
21. Click ``Submit``.
22. To track the cluster status, navigate to the KQueen main dashboard.

To provision a Kubernetes cluster using the Google Kubernetes Engine:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Login in to the Google Kubernetes Engine (https://console.cloud.google.com).
2. Select your Project.
3. Navigate to the ``API’s & Services``  -> ``Credentials`` tab and click ``Create credentials``.
4. From ``Service Account key``, select your service account.
5. Select Json as the key format.
6. Download the Json snippet.
7. Log in to the KQueen web UI.
8. From the ``Create Provisioner`` tab, select ``Google Kubernetes Engine``.
9. Insert the downloaded Json snippet that contains the service account key and submit the provisioner creation.
10. Click ``Deploy Cluster``.
11. Select the defined GCE provisioner.
12. Specify the cluster requirements.
13. Click ``Submit``.
14. To track the cluster status, navigate to the KQueen main dashboard.

To provision a Kubernetes cluster using the Azure Kubernetes Service:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Log in to https://portal.azure.com.
2. Create an Azure Active Directory Application as described in the official Microsoft `Documentation <https://docs.microsoft.com/en-us/azure/azure-resource-manager/resource-group-create-service-principal-portal#create-an-azure-active-directory-application>`_.
3. Copy the Application ID, Application Secret, Tenant ID (Directory ID), and Subscription ID to use in step 8.
4. Set the ``Owner`` role to your Application in the Subscription settings to enable the creation of Kubernetes clusters.
5. Navigate to the ``Resource groups`` tab and create a resource group. Copy the  ‘Resource group name’ to use in step 8.
6. From the to ``Resource groups`` -> your_group -> Access Control (IAM) tab, verify that the Application has the ``Owner`` role in Resource group.
7. Log in to the KQueen web UI.
8. From the ``Create provisioner`` tab, select the AKS engine and set the following:
	1. Set the ``Client ID`` as Application ID from step 3.
	2. Set the ``Resource group name`` as Resource group name from step 4.
	3. Set the ``Secret`` as Application Secret from step 3.
	4. Set the ``Subscription ID`` as  Subscription ID from step 3.
	5. Set the ``Tenant ID`` as Tenant(Directory) ID from step 3.
9. In the KQueen web UI, click ``Deploy Cluster``.
10. Select the AKS provisioner.
11. Specify the cluster requirements.
12. Specify the public SSH key to connect to AKS VM’s. For ssh access into created VM’s, assign the public IP address to the VM as described in `guide <https://gist.github.com/naumvd95/576d6e48200597ca89b26de15e8d3675>`_). Once done, use foollowing command: ``ssh azureuser@<<public_ip>> -i .ssh/your_defined_id_rsa``.
13. Click ``Submit``.
14. To track the cluster status, navigate to the KQueen main dashboard.


.. note::

   The Admin Console in the Azure portal is supported only in Internet Explorer and Microsoft Edge and may fail to operate in other browsers due to Microsoft `issues <https://microsoftintune.uservoice.com/forums/291681-ideas/suggestions/18602776-admin-console-support-on-mac-osx>`_.

.. note::

   The AKS creates a separate resource during the creation of a Kubernetes cluster and uses the defined Resource Group as a prefix. This may affect your billing. For example: 

      .. code-block:: text

         Your Resource Group : Kqueen
         Additional cluster-generated Resource Group: MC_Kqueen_44a37a65-1dff-4ef8-97ca-87fa3b8aee62_eastus

For more information, see `Issues <https://github.com/Azure/AKS/issues/3>`_, and https://docs.microsoft.com/en-us/azure/aks/faq#why-are-two-resource-groups-created-with-aks.


To manually add an existing Kubernetes cluster:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Log in to the KQueen web UI.
2. Create ``Manual Provisioner``.
3. In the ``Create Cluster`` tab choose predefined manual provisioner and attach a valid Kubernetes configuration file.
As a result, the Kubernetes cluster will be attached in a read-only mode.


Backup and recovery ETCD
------------------------

Etcd is the only stateful component of KQueen. To recover etcd in case of a failure, follow the procedure described in https://coreos.com/etcd/docs/latest/v2/admin_guide.html#disaster-recovery.

.. note:: 

   The ``v2`` etcd keys are used in deployment.

Example of etcd backup workflow:

      .. code-block:: bash

         # Backup etcd to directory /root/backup/ (etcd data stored in /var/lib/etcd/default)
         etcdctl backup --data-dir /var/lib/etcd/default --backup-dir /root/backup/


Example of etcd recovery workflow:

      .. code-block:: bash

         # Move data to etcd directory
         mv -v /root/backup/* /var/lib/etcd/default/

         # Start new etcd with these two extra parameters (among the other)
         # for example: etcd --force-new-cluster

.. include:: kqueen.cli_api_examples.rst
