#!/usr/bin/env python3

import requests
import yaml

from kqueen.models import Cluster, Provisioner
from uuid import uuid4

uuid_jenkins = str(uuid4())
uuid_local = str(uuid4())
uuid_provisioner_jenkins = str(uuid4())
uuid_provisioner_local = str(uuid4())
kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico/199/artifact/kubeconfig'



try:
    provisioner = Provisioner(
        id=uuid_provisioner_jenkins,
        name='My AWS',
        engine='kqueen.provisioners.jenkins.JenkinsProvisioner',
        state='OK',
        location='-',
        access_id='demo',
        access_key='Demo123'
    )
    provisioner.save()
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
        engine='local',
        state='OK',
        location='-',
        access_id='',
        access_key=''
    )
    provisioner.save()
except:
    print('Adding aws provisioner failed')


cluster = Cluster(
    id=uuid_local,
    name='local_cluster',
    state='OK',
    provisioner=uuid_provisioner_local,
    kubeconfig=yaml.load(open('kubeconfig_localhost', 'r').read()),
)

print(cluster.kubeconfig.value)
cluster.save()

