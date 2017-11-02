#!/usr/bin/env python3

from kqueen.server import create_app
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User

import requests
import yaml

uuid_organization = '22d8df64-4ac9-4be0-89a7-c45ea0fc85da'

uuid_jenkins = 'c88b05d6-a107-4636-a3cc-eb5c90562f8f'
uuid_local = '2d51891a-adac-4bbc-a725-eed20cc67849'

uuid_provisioner_jenkins = 'e8de24b0-43d1-4a3c-af55-7b1d3f700554'
uuid_provisioner_local = '203c50d6-3d09-4789-8b8b-1ecb00814436'
uuid_provisioner_kubespray = '689de9a2-50e0-4fcd-b6a6-96930b5fadc9'

kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico_sm/33/artifact/kubeconfig'

app = create_app()
with app.app_context():
    # Organization and user
    try:
        organization = Organization(
            id=uuid_organization,
            name='DemoOrg',
            namespace='demoorg'
        )
        organization.save()
    except:
        raise Exception('Adding DemoOrg organization failed')

    try:
        user = User(
            username='admin',
            password='default',
            organization=organization,
        )
        user.save()
    except:
        raise Exception('Adding admin user failed')

    # AWS + Jenkins
    try:
        provisioner = Provisioner(
            id=uuid_provisioner_jenkins,
            name='Jenkins provisioner to AWS',
            state='OK',
            engine='kqueen.engines.JenkinsEngine',
            parameters={
                'username': 'demo',
                'password': 'Demo123'
            }
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding AWS provisioner failed')


    try:
        cluster = Cluster(
            id=uuid_jenkins,
            name='AWS Calico SM 33',
            state='OK',
            provisioner=provisioner,
            kubeconfig=yaml.load(requests.get(kubeconfig_url).text),
        )
        cluster.save()
    except:
        raise Exception('Adding AWS cluster failed')


    # Local cluster
    try:
        provisioner = Provisioner(
            id=uuid_provisioner_local,
            name='Manual provisioner',
            state='OK',
            engine='kqueen.engines.ManualEngine',
            parameters={}
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding manual provisioner failed')


    try:
        cluster = Cluster(
            id=uuid_local,
            name='local_cluster',
            state='OK',
            provisioner=provisioner,
            kubeconfig=yaml.load(open('kubeconfig_localhost', 'r').read()),
        )
        cluster.save()
    except:
        raise Exception('Adding local cluster failed')

    # Dummy Kubespray provisioner
    try:
        provisioner = Provisioner(
            id=uuid_provisioner_kubespray,
            name='Kubespray',
            state='OK',
            engine='kqueen.engines.ManualEngine',
            parameters={}
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding manual provisioner failed')
