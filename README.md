# KaaS
[![Build Status](https://travis-ci.org/Mirantis/kqueen.svg?branch=master)](https://travis-ci.org/Mirantis/kqueen)
[![PyPI version](https://badge.fury.io/py/kqueen.svg)](https://badge.fury.io/py/kqueen)
[![Coverage Status](https://coveralls.io/repos/github/Mirantis/kqueen/badge.svg?branch=master)](https://coveralls.io/github/Mirantis/kqueen?branch=master)

## Development

```
mkvirtualenv -p /usr/bin/python3 kqueen
pip3 install -r requirements.txt
pip3 install --editable .
docker-compose up -d
kqueen
```

## Configuration

We load configuration from file `config_dev.py` by default and this can be configured by `KQUEEN_CONFIG_FILE` environment varialbe.

| Configuration option | Type | Default value | Description |
| --- | --- | --- | --- |

| `KQUEEN_CONFIG_FILE` | Environment variable | `config_dev.py` | Configuration file to load |




## Rationale

Kubernetes is today's probably the most promising container orchestration platform and it is gaining huge momentum. There are many different installation tools and hosted solutions:

* [Kubespray](https://github.com/kubernetes-incubator/kubespray)
* [Kubeadm](https://kubernetes.io/docs/setup/independent/create-cluster-kubeadm/)
* [Kubernetes Salt formula](https://github.com/salt-formulas/salt-formula-kubernetes)


* [Google Container engine](https://cloud.google.com/container-engine)
* [Azure Container Service](https://azure.microsoft.com/en-us/services/container-service/)


There is no need to develop new installation method because we already have many sufficient solutions and Kubernetes instllation isn't a rocket science.
However, there are still customers strugling to integrate Kubernetes because of missing solution for complex orchestration of multiple clusters. In this document we aim to address these problems and propose architecture.

## User stories

I'm application **developer** and I'd like to have a tool to quickly spin-up the cluster and run my application on it. I have multiple applications and need to have multiple clusters for different application. It would be nice to have a possibility to run diffirent application versions in on cluster.

I'm KaaS administration and I need be able to manage all the clusters for our internal customers. I need to list then, control resources and get basic overview about each cluster. I can do administration manualy but I'd like to be able to kill some dead minions and replace them easily. Autoscaling clusters (with predefined range) would be a nice bonus.


## Architecture

We have one central backend service (called *queen*) and this service listens for user requests (via API) and can orchestrate and operate clusters.

### Required actions - MVP

* **Create cluster** - This action will be used to deploy new clusters. However, *queen* service don't deploy cluster on it's own but I uses another service (Jenkins, GKE, ..) to create this cluster.
* **Read cluster information** - Read information about new (and existing) cluster and provide this information to users and administrators. This information must include endpoint for Kubernetes API server and all required credentials (token, basic auth or certificates)
* **Deploy application** - This will connect to cluster and deploy the application. TODO: define format (apply YAMLs, Helm, ...)
* **Delete cluster** - destroy the cluster

### Additional actions

* **Check** - read cluster information and give information about node usage and running workload
* **Scale** - add or remove minions
* **Backup** - backup resources in cluster and provide guidance for PV backup
* **Update** - install newer version of Kubernetes
* **Autoscale** - watch Kubernetes scheduler or pods and start new minions when all existing minions are fully utilized
* **Manage addons** - enable or disable cluster addons

