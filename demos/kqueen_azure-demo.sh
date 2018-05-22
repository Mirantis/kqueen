#!/usr/bin/env bash

################################################
# include the demo-magic script
################################################
# demo-magic.sh is a handy shell script that enables you to script repeatable demos in a bash environment.
# It simulates typing of your commands, so you don't have to type them by yourself when you are presenting.
test -f ./demo-magic.sh || curl --silent https://raw.githubusercontent.com/paxtonhare/demo-magic/master/demo-magic.sh > demo-magic.sh
. ./demo-magic.sh -n

################################################
# Configure the options
################################################

#
# speed at which to simulate typing. bigger num = faster
#
TYPE_SPEED=40

# Uncomment to run non-interactively
export PROMPT_TIMEOUT=0

# No wait after "p" or "pe"
export NO_WAIT=true

#
# custom prompt
#
# see http://www.tldp.org/HOWTO/Bash-Prompt-HOWTO/bash-prompt-escape-sequences.html for escape sequences
#
DEMO_PROMPT="${GREEN}➜ ${CYAN}$ "

docker-compose -f ../docker-compose.yml -f ../docker-compose.demo.yml stop
docker-compose -f ../docker-compose.yml -f ../docker-compose.demo.yml rm -f

# hide the evidence
clear

p  "### KQueen demo with Azure Provisioner"
wait

p  '#'
p  '# Create a new Resource Group:'
wait
pe 'RESOURCE_GROUP_NAME="kqueen-demo-rg"'
pe 'az group create --name "$RESOURCE_GROUP_NAME" --location westeurope'

p  '#'
p  '# Create a service principal that will store permissions to manage resources in the a specified subscription:'
wait
pe 'EMAIL=$(az account list | jq -r ".[].user.name")'
pe 'SUBSCRIPTION_ID=$(az account list | jq -r ".[] | select (.user.name == \"$EMAIL\").id")'
pe 'SERVICE_PRINCIPAL_PASSWORD="my_secret_password"'
pe 'SERVICE_PRINCIPAL_NAME="kqueen-demo-sp"'
pe 'az ad sp create-for-rbac --role="Contributor" --scopes="/subscriptions/$SUBSCRIPTION_ID" --name "$SERVICE_PRINCIPAL_NAME" --password "$SERVICE_PRINCIPAL_PASSWORD"'

p  '#'
p  '# Obtain the Azure parameters to create a provisioner in KQueen:'
wait
pe 'CLIENT_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" | jq -r ".[].appId")'
pe 'TENANT_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" | jq -r ".[].additionalProperties.appOwnerTenantId")'

p  '#'
p  '# Start KQueen and obtain a bearer token:'
wait
pe 'git clone https://github.com/Mirantis/kqueen.git'
pe 'cd kqueen'
pe 'docker-compose -f docker-compose.yml -f docker-compose.demo.yml up -d'
pe 'TOKEN=$(curl -s -H "Content-Type: application/json" --data "{ \"username\": \"admin\", \"password\": \"default\" }" -X POST 127.0.0.1:5000/api/v1/auth | jq -r ".access_token")'
pe 'echo $TOKEN'

p  '#'
p  '# Create a new organization and add a user:'
wait
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testorganization\", \"namespace\": \"testorganization\" }" -X POST 127.0.0.1:5000/api/v1/organizations | jq'
pe 'ORG_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/organizations | jq -r ".[] | select (.name == \"testorganization\").id")'
pe 'echo $ORG_ID'
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"organization\": \"Organization:$ORG_ID\", \"role\": \"superadmin\", \"active\": true, \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/users | jq'

p  '#'
p  '# Switch to the newly created user and add a new Azure Managed Kubernetes Service provisioner:'
wait
pe 'TOKEN=$(curl -s -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/auth | jq -r ".access_token")'
pe 'echo $TOKEN'
pe 'USER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/users | jq -r ".[] | select (.username == \"testusername\").id")'
pe 'echo $USER_ID'
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testprovisioner\", \"engine\": \"kqueen.engines.AksEngine\", \"owner\": \"User:$USER_ID\", \"parameters\": { \"client_id\": \"$CLIENT_ID\", \"resource_group_name\": \"$RESOURCE_GROUP_NAME\", \"secret\": \"$SERVICE_PRINCIPAL_PASSWORD\", \"subscription_id\": \"$SUBSCRIPTION_ID\", \"tenant\": \"$TENANT_ID\" } }" -X POST 127.0.0.1:5000/api/v1/provisioners | jq'

p  '#'
p  '# Deploy a Kubernetes cluster using the AKS provisioner:'
wait
pe 'PROVISIONER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/provisioners | jq -r ".[] | select (.name == \"testprovisioner\").id")'
pe 'echo $PROVISIONER_ID'
pe 'SSH_KEY="$HOME/.ssh/id_rsa.pub"'
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" --data "{ \"name\": \"testcluster\", \"owner\": \"User:$USER_ID\", \"provisioner\": \"Provisioner:$PROVISIONER_ID\", \"metadata\": { \"location\": \"westeurope\", \"node_count\": 1, \"ssh_key\": \"`cat $SSH_KEY`\", \"vm_size\": \"Standard_D1_v2\" } }" -X POST 127.0.0.1:5000/api/v1/clusters | jq'

p  '#'
p  '# Check the status of the cluster by query KQueen API:'
wait
export TOKEN=$(curl -s -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/auth | jq -r ".access_token")
pe 'CLUSTER_ID=$(curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters | jq -r ".[] | select (.name == \"testcluster\").id")'
pe 'echo $CLUSTER_ID'
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters/$CLUSTER_ID | jq ".state"'

p  '#'
p  '# Check the Web Interface of the KQueen and browse the new cluster...'
wait

p  '#'
p  '# Download kubeconfig from KQueen "testcluster":'
wait
pe 'curl -s -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" 127.0.0.1:5000/api/v1/clusters/$CLUSTER_ID/kubeconfig --output kubeconfig-azure.conf'

p  '#'
p  '# Use kubeconfig and check kubernetes:'
wait
pe 'export KUBECONFIG=$PWD/kubeconfig-azure.conf'
pe 'kubectl config view'
pe 'kubectl get nodes'
pe 'kubectl get pods --all-namespaces'

p  '#'
p  '# Install Helm to install application easily:'
wait
pe 'curl https://raw.githubusercontent.com/kubernetes/helm/master/scripts/get | bash'
pe 'kubectl create serviceaccount tiller --namespace kube-system'
pe 'kubectl create clusterrolebinding tiller-cluster-rule --clusterrole=cluster-admin --serviceaccount=kube-system:tiller'
pe 'helm init --upgrade --service-account tiller'
pe 'helm repo update'

p  '#'
p  '# Install Wordpress:'
wait
pe 'helm repo add azure https://kubernetescharts.blob.core.windows.net/azure'
pe 'helm install azure/wordpress --wait --name my-wordpress --set wordpressUsername=admin,wordpressPassword=password,mariadb.enabled=true,mariadb.persistence.size=1Gi,persistence.size=2Gi,resources.requests.cpu=100m'

p  '#'
p  '# Get access details for Wordpress running in Azure k8s and expose the Public IP to AKS:'
wait
export TOKEN=$(curl -s -H "Content-Type: application/json" --data "{ \"username\": \"testusername\", \"password\": \"testpassword\" }" -X POST 127.0.0.1:5000/api/v1/auth | jq -r ".access_token")
pe 'kubectl get svc --namespace default my-wordpress-wordpress'
pe 'kubectl get pods -o wide'
pe 'PUBLIC_IP=$(kubectl get svc --namespace default my-wordpress-wordpress -o jsonpath="{.status.loadBalancer.ingress[0].ip}")'
pe 'DNSNAME="kqueen-demo-wordpress"'
pe "RESOURCEGROUP=$(az network public-ip list --query "[?ipAddress!=null]|[?contains(ipAddress, '$PUBLIC_IP')].[resourceGroup]" --output tsv)"
pe "PIPNAME=$(az network public-ip list --query "[?ipAddress!=null]|[?contains(ipAddress, '$PUBLIC_IP')].[name]" --output tsv)"
pe 'az network public-ip update --resource-group $RESOURCEGROUP --name  $PIPNAME --dns-name $DNSNAME | jq'
pe 'WORDPRESS_FQDN=$(az network public-ip list | jq -r ".[] | select (.ipAddress == \"$PUBLIC_IP\").dnsSettings.fqdn")'
pe 'echo Username: admin'
pe 'echo Password: $(kubectl get secret --namespace default my-wordpress-wordpress -o jsonpath="{.data.wordpress-password}" | base64 --decode)'
pe 'echo http://$WORDPRESS_FQDN/admin'

p  '#'
p  '# Delete Wordpress from k8s'
wait
pe 'kubectl get persistentvolumeclaims'
pe 'kubectl get persistentvolumes'
pe 'helm delete my-wordpress'
pe 'kubectl get persistentvolumeclaims'
pe 'kubectl get persistentvolumes'

p  '# Press ENTER to delete all created resources'
wait

pe 'az ad sp delete --id "$CLIENT_ID"'
pe 'az group delete -y --no-wait --name "$RESOURCE_GROUP_NAME"'
pe 'docker-compose -f docker-compose.yml -f docker-compose.demo.yml stop'
pe 'docker-compose -f docker-compose.yml -f docker-compose.demo.yml rm -f'
pe 'cd .. && rm -rf kqueen'
