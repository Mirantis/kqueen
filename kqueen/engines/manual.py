from .base import BaseEngine
from flask import current_app as app

# Ugly patch to make this module importable outside app context to generate docs
# TODO: fix this by globally importable config
if not app:
    import kqueen.config.dev as config_dev
    app = type(
        'app',
        (object,),
        {'config': {k: v for (k, v) in config_dev.__dict__.items() if not k.startswith("__")}}
    )

class ManualEngine(BaseEngine):
    """
    Manual engine is used for importing existing clusters.
    """

    name = 'manual'
    verbose_name = 'Manual Engine'

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """

        super(ManualEngine, self).__init__(cluster, **kwargs)

    def cluster_list(self):
        """Manual engine don't support list of clusters"""

        return []

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        Returns:
            Cluster:
        """

        return self.cluster

    def provision(self):
        """
        There is no provisioning because Cluster should be already provisioned manually.

        State is updated to OK during in provision method.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """

        self.cluster.state = app.config['CLUSTER_OK_STATE']
        self.cluster.save()

        return (True, None)

    def deprovision(self):
        """
        Deprovision isn't supported by manual engine

        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """

        return (True, None)

    def get_kubeconfig(self):
        """Get kubeconfig of the cluster

        Manual engine don't support any loading of `kubeconfig` so we only return kubeconfig of
        cluster provided during initialization.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """

        return self.cluster.kubeconfig

    def get_parameter_schema(self):
        """Return parameters specific for this Provisioner implementation.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_parameter_schema`
        """

        return {}

    def get_progress(self):
        """
        Manual engine don't report any progress because cluster is already provisioned before
        cluster is imported

        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_progress`
        """

        return {
            'response': 0,
            'progress': 100,
            'result': app.config['CLUSTER_OK_STATE'],
        }

    @staticmethod
    def engine_status():
        """Manual engine is always available.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.engine_status`
        """
        return app.config['PROVISIONER_OK_STATE']
