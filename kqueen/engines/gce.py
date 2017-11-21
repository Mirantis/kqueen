from kqueen.engines.base import BaseEngine
from kqueen.config import current_config


from google.oauth2 import service_account
import googleapiclient.discovery

import os
import logging
import yaml

logger = logging.getLogger(__name__)
config = current_config()


class GceEngine(BaseEngine):
    """
    Google Container Engine
    """
    name = 'gce'
    verbose_name = 'gce'
#    client_id = config.get('GCE_CLIENT_ID')
#    client_secret = config.get('GCE_CLIENT_SECRET')
    service_account_file = 'service_account.json'
    project = 'kqueen-186209'
    zone = 'us-central1-a'
    cluster_config = """
    cluster:
      name: test-cluster
      initialNodeCount: 1
    """

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """
        # Call parent init to save cluster on self
        super(GceEngine, self).__init__(cluster, **kwargs)
        # Client initialization
        self.service_account_file = kwargs.get('service_account_file', self.service_account_file)
        self.project = kwargs.get('project', self.project)
        self.zone = kwargs.get('zone', self.zone)
        self.cluster_config = yaml.load(kwargs.get('cluster_config', self.cluster_config))
        self.client = self._get_client()
        self.cluster_id = "a" + self.cluster.id.replace("-", "")
        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_client(self):
        """
        Initialize Google client
        Construct service account credentials using the service account key file

        """
        credentials = service_account.Credentials.from_service_account_file(self.service_account_file)
        client = googleapiclient.discovery.build('container', 'v1', credentials=credentials)

        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        self.cluster_config["cluster"]["name"] = self.cluster_id
        try:
            create_cluster = self.client.projects().zones().clusters().create(projectId=self.project, zone=self.zone, body=self.cluster_config).execute()
            return (create_cluster, None)
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason: {}'.format(self.cluster_id, repr(e))
            logger.error(msg)
            return (False, msg)
        return (None, None)

    def deprovision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """

        pass

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """

        clusters = self.client.projects().zones().clusters().list(projectId=self.project, zone=self.zone).execute()

        cluster = None
        for i in clusters["clusters"]:
            if self.cluster_id in i["name"]:
                cluster = i

        kubeconfig = {}

        # Get cluster section in KubeConfig
        kubeconfig_cluster_detail = {
            'server': "https://" + cluster["endpoint"],
            'certificate-authority-data': cluster["masterAuth"]["clusterCaCertificate"]
        }

        kubeconfig_cluster = {
            'name': cluster["name"],
            'cluster': kubeconfig_cluster_detail
        }

        user = {}
        user['username'] = cluster["masterAuth"]["username"]
        user['password'] = cluster["masterAuth"]["password"]

        kubeconfig_user = {
            'name': 'admin',
            'user': user
        }

        kubeconfig_context = {
            'name': cluster["name"],
            'context': {
                'cluster': cluster["name"],
                'user': kubeconfig_user["name"],
            },
        }

        kubeconfig = {
            'apiVersion': 'v1',
            'contexts': [kubeconfig_context],
            'clusters': [kubeconfig_cluster],
            'current-context': cluster["name"],
            'kind': 'Config',
            'preferences': {},
            'users': [kubeconfig_user],
        }

        return kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        First we try to get cluster by external_id, because its much more efficient in this
        implementation. If its not possible yet, we return from the slower method
        """
        return self.cluster

    def cluster_list(self):
        """GCE engine don't support list of clusters"""

        return []

    def get_parameter_schema(self):
        """Return parameters specific for this Provisioner implementation.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_parameter_schema`
        """

        return {}

    def get_progress(self):
        """
        GCE engine don't report any progress because cluster is already provisioned before
        cluster is imported

        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_progress`
        """

        return {
            'response': 0,
            'progress': 100,
            'result': config.get('CLUSTER_OK_STATE'),
        }
