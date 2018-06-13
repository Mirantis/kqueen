#!/usr/bin/env python3

from kqueen.server import create_app
from kqueen.models import Cluster

app = create_app()
with app.app_context():
    cluster = Cluster.load('demoorg', '9212695e-3aad-434d-ba26-3403481d37a1')
    print(cluster)
    print(cluster.get_dict())

    print(cluster.engine)
    print(cluster.provisioner.get_engine_cls())
    cluster.engine.provision()
    print(cluster.engine.get_kubeconfig())
