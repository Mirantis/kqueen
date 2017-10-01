#!/usr/bin/env python3

from kqueen.models import Cluster

import requests
import yaml

uuid_jenkins = 'd3d0404c-202e-42b3-88d6-099abdc3d9e9'
uuid_local = 'd3d0404c-202e-42b3-88d6-099abdc3d9e0'
kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico/199/artifact/kubeconfig'


try:
    cluster = Cluster(
        id=uuid_jenkins,
        name='testing',
        provisioner='Manual',
        kubeconfig=yaml.load(requests.get(kubeconfig_url).text),
    )
    cluster.save()
except:
    print('Adding aws cluster failed')


cluster = Cluster(
    id=uuid_local,
    name='local_cluster',
    provisioner='Manual',
    kubeconfig=yaml.load(open('kubeconfig_localhost', 'r').read()),
)
print(cluster.kubeconfig.value)
cluster.save()
