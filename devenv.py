#!/usr/bin/env python3

from kqueen.models import Cluster
from kqueen.models import Provisioner

import requests
import yaml

uuid_jenkins = 'c88b05d6-a107-4636-a3cc-eb5c90562f8f'
uuid_local = '2d51891a-adac-4bbc-a725-eed20cc67849'
uuid_provisioner_jenkins = 'e8de24b0-43d1-4a3c-af55-7b1d3f700554'
uuid_provisioner_local = '203c50d6-3d09-4789-8b8b-1ecb00814436'
kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico_sm/33/artifact/kubeconfig'


try:
    provisioner = Provisioner(
        id=uuid_provisioner_jenkins,
        name='My AWS',
        state='OK',
        engine='kqueen.provisioners.jenkins.JenkinsProvisioner',
        parameters={
            'username': 'demo',
            'password': 'Demo123'
        }
    )
    provisioner.save(check_status=False)
except:
    print('Adding aws provisioner failed')


try:
    cluster = Cluster(
        id=uuid_jenkins,
        name='testing',
        state='OK',
        provisioner=uuid_provisioner_jenkins,
        kubeconfig=yaml.load(requests.get(kubeconfig_url).text),
    )
    cluster.save()
except:
    print('Adding aws cluster failed')


try:
    provisioner = Provisioner(
        id=uuid_provisioner_local,
        name='Manual',
        state='OK',
        engine='local',
        parameters={}
    )
    provisioner.save(check_status=False)
except:
    print('Adding aws provisioner failed')


cluster = Cluster(
    id=uuid_local,
    name='local_cluster',
    state='OK',
    provisioner=uuid_provisioner_local,
    kubeconfig=yaml.load(open('kubeconfig_localhost', 'r').read()),
)

print(cluster.kubeconfig)
cluster.save()
