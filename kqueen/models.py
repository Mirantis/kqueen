from kqueen.storages.etcd import IdField
from kqueen.storages.etcd import Model
from kqueen.storages.etcd import StringField


#
# Model definition
#


class Cluster(Model):
    id = IdField()
    name = StringField()
    provisioner = StringField()
    state = StringField()
    kubeconfig = StringField()

    def status(self):
        """Return information about Kubernetes cluster"""

        return {'nodes': 6}
