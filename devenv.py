#!/usr/bin/env python3

from datetime import datetime
from kqueen.server import create_app
from kqueen.models import Cluster
from kqueen.models import Organization
from kqueen.models import Provisioner
from kqueen.models import User

import requests
import yaml
import os

uuid_organization = '22d8df64-4ac9-4be0-89a7-c45ea0fc85da'

uuid_jenkins = 'c88b05d6-a107-4636-a3cc-eb5c90562f8f'
uuid_local = '2d51891a-adac-4bbc-a725-eed20cc67849'
uuid_gke = '9212695e-3aad-434d-ba26-3403481d37a1'
uuid_aks = 'c02d3b7c-d06e-11e7-973c-68f72873a109'

uuid_provisioner_jenkins = 'e8de24b0-43d1-4a3c-af55-7b1d3f700554'
uuid_provisioner_local = '203c50d6-3d09-4789-8b8b-1ecb00814436'
uuid_provisioner_kubespray = '689de9a2-50e0-4fcd-b6a6-96930b5fadc9'
uuid_provisioner_gke = '516e3a8c-6c4d-49f1-8178-c6f802836618'
uuid_provisioner_aks = 'b72df8cc-d06e-11e7-97cc-68f72873a109'

kubeconfig_url = 'https://ci.mcp.mirantis.net/job/deploy-aws-k8s_ha_calico_sm/17/artifact/kubeconfig'
kubeconfig_file = 'kubeconfig_remote'

app = create_app()
with app.app_context():
    # Organization and user
    try:
        organization = Organization(
            id=uuid_organization,
            name='DemoOrg',
            namespace='demoorg',
            created_at=datetime.utcnow()
        )
        organization.save()
    except:
        raise Exception('Adding DemoOrg organization failed')

    try:
        user = User(
            None,
            username='admin',
            password='default',
            organization=organization,
            created_at=datetime.utcnow(),
            active=True
        )
        user.save()
    except:
        raise Exception('Adding admin user failed')

    # AWS + Jenkins
    try:
        provisioner = Provisioner(
            user.namespace,
            id=uuid_provisioner_jenkins,
            name='Jenkins provisioner to AWS',
            state='OK',
            engine='kqueen.engines.JenkinsEngine',
            parameters={
                'username': 'demo',
                'password': 'Demo123'
            },
            created_at=datetime.utcnow()
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding AWS provisioner failed')

    # GKE provisioner
    try:
        provisioner = Provisioner(
            user.namespace,
            id=uuid_provisioner_gke,
            name='Google Kubernetes engine',
            state='OK',
            engine='kqueen.engines.GceEngine',
            created_at=datetime.utcnow()
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding GKE provisioner failed')

    try:
        cluster = Cluster(
            user.namespace,
            id=uuid_gke,
            state='OK',
            name='GKE clustet, paused',
            provisioner=provisioner,
            created_at=datetime.utcnow()
        )
        cluster.save()
    except:
        raise Exception('Adding GKE provisioner failed')

    # AKS provisioner
    try:
        provisioner = Provisioner(
            user.namespace,
            id=uuid_provisioner_aks,
            name='Azure Kubernetes Service',
            state='OK',
            engine='kqueen.engines.AksEngine',
            created_at=datetime.utcnow()
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding AKS provisioner failed')

    try:
        cluster = Cluster(
            user.namespace,
            id=uuid_aks,
            state='OK',
            name='AKS clustet, paused',
            provisioner=provisioner,
            created_at=datetime.utcnow()
        )
        cluster.save()
    except:
        raise Exception('Adding AKS cluster failed')

    try:
        # load kubeconfig file
        if os.path.isfile(kubeconfig_file):
            print('Loading remote kubeconfig from {}'.format(kubeconfig_file))
            kubeconfig = yaml.load(open(kubeconfig_file).read())
        else:
            print('Loading remote kubeconfig from {}'.format(kubeconfig_url))
            kubeconfig = yaml.load(requests.get(kubeconfig_url).text)

        cluster = Cluster(
            user.namespace,
            id=uuid_jenkins,
            name='AWS kqueen testing',
            state='OK',
            provisioner=provisioner,
            kubeconfig=kubeconfig,
            created_at=datetime.utcnow()
        )
        cluster.save()
    except:
        raise Exception('Adding AWS cluster failed')


    # Local cluster
    try:
        provisioner = Provisioner(
            user.namespace,
            id=uuid_provisioner_local,
            name='Manual provisioner',
            state='OK',
            engine='kqueen.engines.ManualEngine',
            parameters={},
            created_at=datetime.utcnow()
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding manual provisioner failed')


    try:
        cluster = Cluster(
            user.namespace,
            id=uuid_local,
            name='local_cluster',
            state='OK',
            provisioner=provisioner,
            kubeconfig=yaml.load(open('kubeconfig_localhost', 'r').read()),
            created_at=datetime.utcnow()
        )
        cluster.save()
    except:
        raise Exception('Adding local cluster failed')

    # Dummy Kubespray provisioner
    try:
        provisioner = Provisioner(
            user.namespace,
            id=uuid_provisioner_kubespray,
            name='Kubespray',
            state='OK',
            engine='kqueen.engines.ManualEngine',
            parameters={},
            created_at=datetime.utcnow()
        )
        provisioner.save(check_status=False)
    except:
        raise Exception('Adding manual provisioner failed')
