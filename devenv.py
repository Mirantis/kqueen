#!/usr/bin/env python3

from kqueen.models import Cluster

import requests
import yaml

uuid = 'd3d0404c-202e-42b3-88d6-099abdc3d9e9'
kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico/199/artifact/kubeconfig'


cluster = Cluster(
    id=uuid,
    name='testing',
    provisioner='Manual',
    kubeconfig=yaml.load(requests.get(kubeconfig_url).text),
)
cluster.save()
