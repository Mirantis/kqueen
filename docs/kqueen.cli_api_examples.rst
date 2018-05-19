KQueen CLI API examples
-----------------------

This section lists the available KQueen API operations that you can perform
through the command-line interface and provides examples.

**To obtain a bearer token and authenticate to KQueen:**

.. code-block:: bash

   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "admin", "password": "default" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN


**To list the organizations:**

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/organizations | jq
   [
     {
       "created_at": "2018-05-03T14:08:35",
       "id": "22d8df64-4ac9-4be0-89a7-c45ea0fc85da",
       "name": "DemoOrg",
       "namespace": "demoorg"
     }
   ]


**To check the clusters:**

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/clusters | jq
   []


**To list the provisioners:**

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/provisioners/engines
   ...


**To list users:**

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" 127.0.0.1:5000/api/v1/users | jq
   [
     {
       "active": true,
       "created_at": "2018-05-03T14:08:35",
       "email": "admin@kqueen.net",
       "id": "09587e34-812d-4efc-af17-fbfd7315674c",
       "organization": {
         "created_at": "2018-05-03T14:08:35",
         "id": "22d8df64-4ac9-4be0-89a7-c45ea0fc85da",
         "name": "DemoOrg",
         "namespace": "demoorg"
       },
       "password": "$2b$12$DQvL0Wsqr10DJovkNXvqXeZeAImoqmPXQHZF2nsZ0ICcB6WNBlwtS",
       "role": "superadmin",
       "username": "admin"
     }
   ]


**To create a new organization:**

The following command uses ``testorganization`` as an example.

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data '{ "name": "testorganization", "namespace": "testorganization" }' -X POST 127.0.0.1:5000/api/v1/organizations | jq
   {
     "created_at": "2018-05-03T14:10:09",
     "id": "bebf0186-e2df-40a7-9b89-a2b77a7275d9",
     "name": "testorganization",
     "namespace": "testorganization"
   }


**To add a new user and password to the new organization:**

The following example shows how to add the ``testusername`` user name and
``testpassword`` password to the newly created ``testorganization`` organization.

.. code-block:: bash

   $ ORG_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"  127.0.0.1:5000/api/v1/organizations | jq -r '.[] | select (.name == "testorganization").id')
   $ echo $ORG_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"organization\": \"Organization:$ORG_ID\", \"role\": \"superadmin\", \"active\": true, \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/users | jq
   {
     "active": true,
     "created_at": "2018-05-03T14:10:33",
     "id": "c2782be5-8b87-4322-82b0-6b726bc4952d",
     "organization": {
       "created_at": "2018-05-03T14:10:09",
       "id": "bebf0186-e2df-40a7-9b89-a2b77a7275d9",
       "name": "testorganization",
       "namespace": "testorganization"
     },
     "password": "$2b$12$gYhVf23WXplWSZH8FjaiB.9SzwsRHAelipx2bLF407E0zAOGnmfNC",
     "role": "superadmin",
     "username": "testusername"
   }


**To switch to a particular user:**

The following example shows how to switch to the ``testusername`` user.


.. code-block:: bash

   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "testusername", "password": "testpassword" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN


**To add a new Azure Managed Kubernetes Service provisioner:**

The following example shows how to add a new Azure Managed Kubernetes Service
provisioner created by the ``testusername`` user.

.. code-block:: bash

   $ USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/users | jq -r '.[] | select (.username == "testusername").id')
   $ echo $USER_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testprovisioner\", \"engine\": \"kqueen.engines.AksEngine\", \"owner\": \"User:$USER_ID\", \"parameters\": { \"client_id\": \"testclient_id\", \"resource_group_name\": \"testresource_group_name\", \"secret\": \"testsecret\", \"subscription_id\": \"testsubscription_id\", \"tenant\": \"testtenant\" } }" -X POST 127.0.0.1:5000/api/v1/provisioners | jq
   {
     "created_at": "2018-05-03T14:11:08",
     "engine": "kqueen.engines.AksEngine",
     "id": "052397f1-b813-49ac-acc8-812c9e00b709",
     "name": "testprovisioner",
     "owner": {
       "active": true,
       "created_at": "2018-05-03T14:10:33",
       "id": "c2782be5-8b87-4322-82b0-6b726bc4952d",
       "organization": {
         "created_at": "2018-05-03T14:10:09",
         "id": "bebf0186-e2df-40a7-9b89-a2b77a7275d9",
         "name": "testorganization",
         "namespace": "testorganization"
       },
       "password": "$2b$12$gYhVf23WXplWSZH8FjaiB.9SzwsRHAelipx2bLF407E0zAOGnmfNC",
       "role": "superadmin",
       "username": "testusername"
     },
     "parameters": {
       "client_id": "testclient_id",
       "resource_group_name": "testresource_group_name",
       "secret": "testsecret",
       "subscription_id": "testsubscription_id",
       "tenant": "testtenant"
     },
     "state": "OK",
     "verbose_name": "Azure Managed Kubernetes Service"
   }


**To deploy a new Kubernetes cluster using Azure Managed Kubernetes Service provisioner:** 

The following example shows how to deploy a new Kubernetes cluster using the
Azure Managed Kubernetes Service provisioner ``testprovisioner`` created by
the ``testusername`` user.

.. code-block:: bash

   $ PROVISIONER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/provisioners | jq -r '.[] | select (.name == "testprovisioner").id')
   $ echo $USER_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testcluster\", \"owner\": \"User:$USER_ID\", \"provisioner\": \"Provisioner:$PROVISIONER_ID\", \"metadata\": { \"location\": \"eastus\", \"ssh_key\": \"testssh_key\", \"vm_size\": \"Standard_D1_v2\" } }" -X POST 127.0.0.1:5000/api/v1/clusters | jq
   ...


**To check the clusters:**

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters | jq
   ...
