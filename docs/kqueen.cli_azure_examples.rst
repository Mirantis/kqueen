Azure CLI operations with KQueen
--------------------------------

In KQueen, you can perform a number of Azure operations using the command-line interface (CLI).
For example, you can create an Azure account, create a new Kubernetes cluster (AKS), download the Kubernetes configuration file and use it to push an application into Kubernetes.


Configure Azure to work with KQueen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

#. Log in to your Azure portal:

.. code-block:: bash

   $ az login
   To sign in, use a web browser to open the page https://microsoft.com/devicelogin and enter the code CBMZ4QPTE to authenticate.
   [
     {
       "cloudName": "AzureCloud",
       "id": "8xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx2",
       "isDefault": true,
       "name": "Pay-As-You-Go",
       "state": "Enabled",
       "tenantId": "7xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxd",
       "user": {
         "name": "kxxxxxxxxxxxxxxxxxxxxxxxm",
         "type": "user"
       }
     }
   ]

#. Create a new Resource Group:

.. code-block:: bash

   $ RESOURCE_GROUP_NAME="kqueen-demo-rg"
   $ az group create --name "$RESOURCE_GROUP_NAME" --location westeurope
   {
     "id": "/subscriptions/8xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx2/resourceGroups/kqueen-demo-rg",
     "location": "westeurope",
     "managedBy": null,
     "name": "kqueen-demo-rg",
     "properties": {
       "provisioningState": "Succeeded"
     },
     "tags": null
   }

#. Create a service principal that will store permissions to manage resources in the a specified subscription:

.. code-block:: bash

   $ EMAIL=$(az account list | jq -r '.[].user.name')
   $ SUBSCRIPTION_ID=$(az account list | jq -r ".[] | select (.user.name == \"$EMAIL\").id")
   $ SECRET="my_password"
   $ SERVICE_PRINCIPAL_NAME="kqueen-demo-sp"
   $ az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/$SUBSCRIPTION_ID" --name "$SERVICE_PRINCIPAL_NAME" --password "$SECRET"

#. Obtain the Azure parameters to create a provisioner in KQueen:

.. code-block:: bash

   $ CLIENT_ID="$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" | jq -r '.[].appId')"
   $ TENANT_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" | jq -r '.[].additionalProperties.appOwnerTenantId')


Create and configure a Azure Kubernetes cluster using KQueen
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

In this procedure we use "testorganization" and "testuser / testpassword" as examples.

#. Start KQueen and obtain a bearer token:

.. code-block:: bash

   $ git clone https://github.com/Mirantis/kqueen.git
   $ cd kqueen
   $ docker-compose -f docker-compose.yml -f docker-compose.demo.yml rm -f # Make sure you are starting from scratch
   $ docker-compose -f docker-compose.yml -f docker-compose.demo.yml up
   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "admin", "password": "default" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN

#. Create a new organization and add a user:

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data '{ "name": "testorganization", "namespace": "testorganization" }' -X POST 127.0.0.1:5000/api/v1/organizations | jq
   $ ORG_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json"  127.0.0.1:5000/api/v1/organizations | jq -r '.[] | select (.name == "testorganization").id')
   $ echo $ORG_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"organization\": \"Organization:$ORG_ID\", \"role\": \"superadmin\", \"active\": true, \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/users | jq

#. Switch to the newly created user and add a new Azure Managed Kubernetes Service provisioner:

.. code-block:: bash

   $ TOKEN=$(curl -s -H "Content-Type: application/json" --data '{ "username": "testusername", "password": "testpassword" }' -X POST 127.0.0.1:5000/api/v1/auth | jq -r '.access_token')
   $ echo $TOKEN
   $ USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/users | jq -r '.[] | select (.username == "testusername").id')
   $ echo $USER_ID
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testprovisioner\", \"engine\": \"kqueen.engines.AksEngine\", \"owner\": \"User:$USER_ID\", \"parameters\": { \"client_id\": \"$CLIENT_ID\", \"resource_group_name\": \"$RESOURCE_GROUP_NAME\", \"secret\": \"$SECRET\", \"subscription_id\": \"$SUBSCRIPTION_ID\", \"tenant\": \"$TENANT_ID\" } }" -X POST 127.0.0.1:5000/api/v1/provisioners | jq

#. Deploy a Kubernetes cluster using the AKS provisioner:

.. code-block:: bash

   $ PROVISIONER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/provisioners | jq -r '.[] | select (.name == "testprovisioner").id')
   $ echo $PROVISIONER_ID
   $ SSH_KEY="$HOME/.ssh/id_rsa.pub"
   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testcluster\", \"owner\": \"User:$USER_ID\", \"provisioner\": \"Provisioner:$PROVISIONER_ID\", \"metadata\": { \"location\": \"westeurope\", \"node_count\": 1, \"ssh_key\": \"`cat $SSH_KEY`\", \"vm_size\": \"Standard_D1_v2\" } }" -X POST 127.0.0.1:5000/api/v1/clusters | jq

#. Check the status of the cluster by query KQueen API (run this command multiple times):

.. code-block:: bash

   $ CLUSTER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters | jq -r '.[] | select (.name == "testcluster").id')
   $ echo $CLUSTER_ID
   $ watch "curl -s -H \"Authorization: Bearer $TOKEN\" -H 'Content-Type: application/json' 127.0.0.1:5000/api/v1/clusters/$CLUSTER_ID | jq '.state'"
   "Deploying"
   ...
   "OK"

# Check the cluster details in the Web GUI.

#. Download kubeconfig from KQueen "testcluster":

.. code-block:: bash

   $ curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters/$CLUSTER_ID/kubeconfig --output kubeconfig.conf
   $ head kubeconfig.conf

#. Use kubeconfig and check kubernetes:

.. code-block:: bash

   $ export KUBECONFIG=$PWD/kubeconfig.conf

   $ kubectl get nodes
   NAME                       STATUS    ROLES     AGE       VERSION
   aks-agentpool-21742512-0   Ready     agent     11m       v1.7.7

   $ kubectl describe nodes aks-agentpool-21742512-0
   Name:               aks-agentpool-21742512-0
   Roles:              agent
   Labels:             agentpool=agentpool
                       beta.kubernetes.io/arch=amd64
                       beta.kubernetes.io/instance-type=Standard_D1_v2
                       beta.kubernetes.io/os=linux
                       failure-domain.beta.kubernetes.io/region=westeurope
                       failure-domain.beta.kubernetes.io/zone=0
                       kubernetes.azure.com/cluster=MC_kqueen-demo-rg_4b0363bf-0c74-4cc3-9468-23a79e0a2ec2_westeuro
                       kubernetes.io/hostname=aks-agentpool-21742512-0
                       kubernetes.io/role=agent
                       storageprofile=managed
                       storagetier=Standard_LRS
   Annotations:        node.alpha.kubernetes.io/ttl=0
                       volumes.kubernetes.io/controller-managed-attach-detach=true
   CreationTimestamp:  Thu, 17 May 2018 09:12:32 +0200
   Taints:             <none>
   Unschedulable:      false
   Conditions:
     Type                 Status  LastHeartbeatTime                 LastTransitionTime                Reason                       Message
     ----                 ------  -----------------                 ------------------                ------                       -------
     NetworkUnavailable   False   Thu, 17 May 2018 09:13:10 +0200   Thu, 17 May 2018 09:13:10 +0200   RouteCreated                 RouteController created a route
     OutOfDisk            False   Thu, 17 May 2018 09:21:33 +0200   Thu, 17 May 2018 09:12:32 +0200   KubeletHasSufficientDisk     kubelet has sufficient disk space available
     MemoryPressure       False   Thu, 17 May 2018 09:21:33 +0200   Thu, 17 May 2018 09:12:32 +0200   KubeletHasSufficientMemory   kubelet has sufficient memory available
     DiskPressure         False   Thu, 17 May 2018 09:21:33 +0200   Thu, 17 May 2018 09:12:32 +0200   KubeletHasNoDiskPressure     kubelet has no disk pressure
     Ready                True    Thu, 17 May 2018 09:21:33 +0200   Thu, 17 May 2018 09:12:57 +0200   KubeletReady                 kubelet is posting ready status. AppArmor enabled
   Addresses:
     InternalIP:  10.240.0.4
     Hostname:    aks-agentpool-21742512-0
   Capacity:
    alpha.kubernetes.io/nvidia-gpu:  0
    cpu:                             1
    memory:                          3501580Ki
    pods:                            110
   Allocatable:
    alpha.kubernetes.io/nvidia-gpu:  0
    cpu:                             1
    memory:                          3399180Ki
    pods:                            110
   System Info:
    Machine ID:                 df3ffcd7ab1347709fce4c012f61baba
    System UUID:                8B317B9A-D6E6-D846-B6FB-F8B396AA5AFF
    Boot ID:                    1d97c041-54fd-4d80-8515-2e3ef0f2f96c
    Kernel Version:             4.13.0-1012-azure
    OS Image:                   Ubuntu 16.04.4 LTS
    Operating System:           linux
    Architecture:               amd64
    Container Runtime Version:  docker://1.13.1
    Kubelet Version:            v1.7.7
    Kube-Proxy Version:         v1.7.7
   PodCIDR:                     10.244.0.0/24
   ExternalID:                  /subscriptions/8xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxx2/resourceGroups/MC_kqueen-demo-rg_4b0363bf-0c74-4cc3-9468-23a79e0a2ec2_westeurope/providers/Microsoft.Compute/virtualMachines/aks-agentpool-21742512-0
   ProviderID:                  azure:///subscriptions/8xxxxxxx-xxxx-xxxx-xxxxxxxxxxxxxxxx2/resourceGroups/MC_kqueen-demo-rg_4b0363bf-0c74-4cc3-9468-23a79e0a2ec2_westeurope/providers/Microsoft.Compute/virtualMachines/aks-agentpool-21742512-0
   Non-terminated Pods:         (7 in total)
     Namespace                  Name                                     CPU Requests  CPU Limits  Memory Requests  Memory Limits
     ---------                  ----                                     ------------  ----------  ---------------  -------------
     kube-system                heapster-186967039-7w028                 138m (13%)    138m (13%)  294Mi (8%)       294Mi (8%)
     kube-system                kube-dns-v20-2253765213-nq8vz            110m (11%)    0 (0%)      120Mi (3%)       220Mi (6%)
     kube-system                kube-dns-v20-2253765213-pn3dd            110m (11%)    0 (0%)      120Mi (3%)       220Mi (6%)
     kube-system                kube-proxy-lgv61                         100m (10%)    0 (0%)      0 (0%)           0 (0%)
     kube-system                kube-svc-redirect-sw2sx                  0 (0%)        0 (0%)      0 (0%)           0 (0%)
     kube-system                kubernetes-dashboard-2898242510-070c5    100m (10%)    100m (10%)  50Mi (1%)        50Mi (1%)
     kube-system                tunnelfront-440375991-xdftj              0 (0%)        0 (0%)      0 (0%)           0 (0%)
   Allocated resources:
     (Total limits may be over 100 percent, i.e., overcommitted.)
     CPU Requests  CPU Limits  Memory Requests  Memory Limits
     ------------  ----------  ---------------  -------------
     558m (55%)    238m (23%)  584Mi (17%)      784Mi (23%)
   Events:
     Type    Reason                   Age               From                                  Message
     ----    ------                   ----              ----                                  -------
     Normal  Starting                 12m               kubelet, aks-agentpool-21742512-0     Starting kubelet.
     Normal  NodeAllocatableEnforced  12m               kubelet, aks-agentpool-21742512-0     Updated Node Allocatable limit across pods
     Normal  NodeHasSufficientDisk    9m (x5 over 12m)  kubelet, aks-agentpool-21742512-0     Node aks-agentpool-21742512-0 status is now: NodeHasSufficientDisk
     Normal  NodeHasSufficientMemory  9m (x5 over 12m)  kubelet, aks-agentpool-21742512-0     Node aks-agentpool-21742512-0 status is now: NodeHasSufficientMemory
     Normal  NodeHasNoDiskPressure    9m (x5 over 12m)  kubelet, aks-agentpool-21742512-0     Node aks-agentpool-21742512-0 status is now: NodeHasNoDiskPressure
     Normal  Starting                 8m                kube-proxy, aks-agentpool-21742512-0  Starting kube-proxy.
     Normal  NodeReady                8m                kubelet, aks-agentpool-21742512-0     Node aks-agentpool-21742512-0 status is now: NodeReady

   $ kubectl get all --all-namespaces
   NAMESPACE     NAME                                        READY     STATUS    RESTARTS   AGE
   kube-system   pod/heapster-186967039-7w028                2/2       Running   0          9m
   kube-system   pod/kube-dns-v20-2253765213-nq8vz           3/3       Running   0          11m
   kube-system   pod/kube-dns-v20-2253765213-pn3dd           3/3       Running   0          11m
   kube-system   pod/kube-proxy-lgv61                        1/1       Running   0          11m
   kube-system   pod/kube-svc-redirect-sw2sx                 1/1       Running   0          11m
   kube-system   pod/kubernetes-dashboard-2898242510-070c5   1/1       Running   0          11m
   kube-system   pod/tunnelfront-440375991-xdftj             1/1       Running   0          11m

   NAMESPACE     NAME                                         DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
   kube-system   deployment.extensions/heapster               1         1         1            1           11m
   kube-system   deployment.extensions/kube-dns-v20           2         2         2            2           11m
   kube-system   deployment.extensions/kubernetes-dashboard   1         1         1            1           11m
   kube-system   deployment.extensions/tunnelfront            1         1         1            1           11m

   NAMESPACE     NAME                                                    DESIRED   CURRENT   READY     AGE
   kube-system   replicaset.extensions/heapster-186967039                1         1         1         9m
   kube-system   replicaset.extensions/heapster-482310450                0         0         0         11m
   kube-system   replicaset.extensions/kube-dns-v20-2253765213           2         2         2         11m
   kube-system   replicaset.extensions/kubernetes-dashboard-2898242510   1         1         1         11m
   kube-system   replicaset.extensions/tunnelfront-440375991             1         1         1         11m

   NAMESPACE     NAME                                   DESIRED   CURRENT   UP-TO-DATE   AVAILABLE   AGE
   kube-system   deployment.apps/heapster               1         1         1            1           11m
   kube-system   deployment.apps/kube-dns-v20           2         2         2            2           11m
   kube-system   deployment.apps/kubernetes-dashboard   1         1         1            1           11m
   kube-system   deployment.apps/tunnelfront            1         1         1            1           11m

#. Install `Helm <http://helm.sh/>`_ to install application easily:

.. code-block:: bash

   $ curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash
   $ kubectl create serviceaccount tiller --namespace kube-system
   $ kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller
   $ helm init --upgrade --service-account tiller
   $ helm repo update

#. Install `Wordpress <https://github.com/Azure/helm-charts/tree/master/wordpress>`_:

.. code-block:: bash

   $ helm repo add azure https://kubernetescharts.blob.core.windows.net/azure
   $ helm install azure/wordpress --name my-wordpress --set wordpressUsername=admin,wordpressPassword=password,mariadb.enabled=true,mariadb.persistence.enabled=false,persistence.enabled=false,resources.requests.cpu=100m
   $ sleep 300

#. Get access details for Wordpress running in Azure k8s and expose the Public IP to AKS:

.. code-block:: bash

   $ kubectl get svc --namespace default my-wordpress-wordpress
   $ kubectl get pods -o wide
   $ PUBLIC_IP=$(kubectl get svc --namespace default my-wordpress-wordpress -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
   $ DNSNAME="kqueen-demo-wordpress"
   $ RESOURCEGROUP=$(az network public-ip list --query "[?ipAddress!=null]|[?contains(ipAddress, '$PUBLIC_IP')].[resourceGroup]" --output tsv)
   $ PIPNAME=$(az network public-ip list --query "[?ipAddress!=null]|[?contains(ipAddress, '$PUBLIC_IP')].[name]" --output tsv)
   $ az network public-ip update --resource-group $RESOURCEGROUP --name  $PIPNAME --dns-name $DNSNAME | jq
   $ WORDPRESS_FQDN=$(az network public-ip list | jq -r ".[] | select (.ipAddress == \"$SERVICE_IP\").dnsSettings.fqdn")
   $ echo Username: admin
   $ echo Password: $(kubectl get secret --namespace default my-wordpress-wordpress -o jsonpath="{.data.wordpress-password}" | base64 --decode)
   $ echo http://$WORDPRESS_FQDN/admin


Clean up all Azure resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   $ az ad sp delete --id "$CLIENT_ID"
   $ az group delete -y --no-wait --name "$RESOURCE_GROUP_NAME"

