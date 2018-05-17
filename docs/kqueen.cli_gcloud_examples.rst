Google Cloud CLI operations with KQueen
---------------------------------------

In KQueen, you can perform a number of Google Cloud operations using the command-line interface (CLI).
For example, you can create a Google Cloud account, create a new Kubernetes cluster (GKE), download the kubeconfig and use it to push an application into Kubernetes.

Configure Google Cloud Engine to work with KQueen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Create a Google Cloud account and configure the `gcloud` tool to access your GCE:

https://cloud.google.com/sdk/gcloud/reference/init

#. Log in to Google Cloud:

.. code-block:: bash

   $ cd /tmp/
   $ gcloud init

#. Create new project in GCE:

.. code-block:: bash

   $ GCE_PROJECT_NAME="My Test Project"
   $ GCE_PROJECT_ID="my-test-project-`date +%F`"
   $ gcloud projects create "$GCE_PROJECT_ID" --name "$GCE_PROJECT_NAME"
   Create in progress for [https://cloudresourcemanager.googleapis.com/v1/projects/my-test-project-2018-05-11].
   Waiting for [operations/cp.7874714971502871878] to finish...done.

#. Set new project as default:

.. code-block:: bash

   $ gcloud config set project $GCE_PROJECT_ID

#. Enable Billing for the project:

   $ GCE_ACCOUNT_ID=$(gcloud beta billing accounts list --filter="My Billing Account" --format="value(ACCOUNT_ID)")
   $ gcloud billing projects link "$GCE_PROJECT_ID" --billing-account="$GCE_ACCOUNT_ID"

#. Create Service Account and assign proper rights to it:

.. code-block:: bash

   $ GCE_SERVICE_ACCOUNT_DISPLAY_NAME="My_Service_Account"
   $ GCE_SERVICE_ACCOUNT_NAME="my-service-account"
   $ gcloud iam service-accounts create "$GCE_SERVICE_ACCOUNT_NAME" --display-name "$GCE_SERVICE_ACCOUNT_DISPLAY_NAME"

#. Generate keys for new service account:

.. note:: Keep the generated key.json file in a safe location.

.. code-block:: bash

   $ GCE_SERVICE_ACCOUNT_EMAIL=$(gcloud iam service-accounts list --filter="$GCE_SERVICE_ACCOUNT_NAME" --format="value(email)")
   $ gcloud iam service-accounts keys create --iam-account $GCE_SERVICE_ACCOUNT_EMAIL key.json

#. Assign a role to the service account and bind it to the project:

.. code-block:: bash

   $ GCE_EMAIL="your_email_address@gmail.com"
   $ gcloud iam service-accounts add-iam-policy-binding "$GCE_SERVICE_ACCOUNT_EMAIL" --member="user:$GCE_EMAIL" --role="roles/owner"
   $ gcloud projects add-iam-policy-binding $GCE_PROJECT_ID --member="serviceAccount:$GCE_SERVICE_ACCOUNT_EMAIL" --role="roles/container.clusterAdmin"
   $ gcloud projects add-iam-policy-binding $GCE_PROJECT_ID --member="serviceAccount:$GCE_SERVICE_ACCOUNT_EMAIL" --role="roles/iam.serviceAccountActor"

Create and configure a GCE cluster using KQueen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Start KQueen and obtain bearer token:

.. code-block:: bash

   $ git clone https://github.com/Mirantis/kqueen.git
   $ cd kqueen
   $ docker-compose -f docker-compose.yml -f docker-compose.demo.yml rm -f # Make sure you are starting from scratch
   $ docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "admin", "password": "default" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN

#. Create new organization "testorganization" with new user / password "testusername / testpassword":

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data '{ "name": "testorganization", "namespace": "testorganization" }' -X POST 127.0.0.1:5000/api/v1/organizations | jq
   $ ORG_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"  127.0.0.1:5000/api/v1/organizations | jq -r '.[] | select (.name == "testorganization").id')
   $ echo $ORG_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"organization\": \"Organization:$ORG_ID\", \"role\": \"superadmin\", \"active\": true, \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/users | jq

#. Switch to new user "testusername" and add new Google Cloud Kubernetes Service provisioner:

.. code-block:: bash

   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "testusername", "password": "testpassword" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN
   $ USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/users | jq -r '.[] | select (.username == "testusername").id')
   $ echo $USER_ID
   $ SERVICE_ACCOUNT_INFO=$(cat ../key.json)
   $ echo $SERVICE_ACCOUNT_INFO
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testprovisioner\", \"engine\": \"kqueen.engines.GceEngine\", \"owner\": \"User:$USER_ID\", \"parameters\": { \"project\": \"$GCE_PROJECT_ID\", \"service_account_info\": $SERVICE_ACCOUNT_INFO } }" -X POST 127.0.0.1:5000/api/v1/provisioners | jq

#. Deploy Kubernetes cluster using the GKE provisioner:

.. code-block:: bash

   $ PROVISIONER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/provisioners | jq -r '.[] | select (.name == "testprovisioner").id')
   $ echo $PROVISIONER_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testcluster\", \"owner\": \"User:$USER_ID\", \"provisioner\": \"Provisioner:$PROVISIONER_ID\", \"metadata\": { \"machine_type\": \"n1-standard-1\", \"node_count\": 1, \"zone\": \"us-central1-a\" } }" -X POST 127.0.0.1:5000/api/v1/clusters | jq

#. Check the status of the cluster by query KQueen API (run this command multiple times):

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters

#. Download kubeconfig from KQueen "testcluster":

.. code-block:: bash

   $ CLUSTER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters | jq -r '.[] | select (.name == "testcluster").id')
   $ echo $CLUSTER_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters/$CLUSTER_ID/kubeconfig > kubeconfig.conf

#. Use kubeconfig and check kubernetes:

.. code-block:: bash

   $ export KUBECONFIG=$PWD/kubeconfig.conf
   $ kubectl get nodes
   $ kubectl get componentstatuses
   $ kubectl get namespaces

#. Install `Helm <http://helm.sh/>`_ to install application easily:

.. code-block:: bash

   $ curl -s $(curl -s https://github.com/kubernetes/helm | awk -F \" "/linux-amd64/ { print \$2 }") | tar xvzf - -C /tmp/ linux-amd64/helm
   $ sudo mv /tmp/linux-amd64/helm /usr/local/bin/
   $ kubectl create serviceaccount tiller --namespace kube-system
   $ kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
   $ helm init --service-account tiller
   $ sleep 30
   $ helm repo update

#. You can easily install the apps to utilize the cluster using Helm:

.. code-block:: bash

   $ helm install stable/kubernetes-dashboard --name=my-kubernetes-dashboard --namespace monitoring --set ingress.enabled=true,rbac.clusterAdminRole=true
