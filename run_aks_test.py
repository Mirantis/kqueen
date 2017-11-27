#!/usr/bin/env python3

from kqueen.server import create_app
from kqueen.models import Cluster

app = create_app()
with app.app_context():
    cluster = Cluster.load('demoorg', 'c02d3b7c-d06e-11e7-973c-68f72873a109')
    print(cluster)
    print(cluster.get_dict())

    print(cluster.engine)
    print(cluster.provisioner.get_engine_cls())
#    cluster.engine.provision()
    print(cluster.engine.get_kubeconfig())
#    cluster.engine.deprovision()
