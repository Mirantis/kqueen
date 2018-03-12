from google.oauth2 import service_account
from kqueen.config import current_config
from kqueen.engines.base import BaseEngine

import googleapiclient.discovery
import logging
import requests

logger = logging.getLogger('kqueen_api')
config = current_config()


STATE_MAP = {
    'PROVISIONING': config.get('CLUSTER_PROVISIONING_STATE'),
    'RUNNING': config.get('CLUSTER_OK_STATE'),
    'STOPPING': config.get('CLUSTER_DEPROVISIONING_STATE'),
    'RECONCILING': config.get('CLUSTER_RESIZING_STATE')
}


class GceEngine(BaseEngine):
    """
    Google Container Engine
    """
    name = 'gce'
    verbose_name = 'Google Kubernetes Engine'
    # TODO: only subset of possible choices for zone are listed in parameter_schema,
    # we could add more later, here is the list of possible choices:
    # https://cloud.google.com/compute/docs/regions-zones/
    # TODO: only subset of possible choices for machine_type are listed in parameter_schema,
    # we could add more later, here is the list of possible choices:
    # https://cloud.google.com/compute/docs/machine-types
    parameter_schema = {
        'provisioner': {
            'service_account_info': {
                'type': 'json_file',
                'label': 'Service Account File (JSON)',
                'validators': {
                    'required': True,
                    'jsonfile': [
                        'private_key_id',
                        'private_key',
                        'client_email',
                        'client_id',
                        'auth_uri',
                        'token_uri'
                    ]
                }
            }
        },
        'cluster': {
            'node_count': {
                'type': 'integer',
                'label': 'Node Count',
                'default': 1,
                'validators': {
                    'required': True,
                    'min': 1,
                    'number': True
                }
            },
            'zone': {
                'type': 'select',
                'label': 'Zone',
                'choices': [
                    ('us-central1-a', 'US - Central 1 - A'),
                    ('us-west1-a', 'US - West 1 - A'),
                    ('us-east1-b', 'US - East 1 - B'),
                    ('us-east4-a', 'US - East 4 - A'),
                    ('northamerica-northeast1-a', 'North America - Northeast 1 - A'),
                    ('southamerica-east1-a', 'South America - East 1 - A'),
                    ('europe-west1-b', 'Europe - West 1 - B'),
                    ('europe-west2-a', 'Europe - West 2 - A'),
                    ('europe-west3-a', 'Europe - West 3 - A'),
                    ('europe-west4-b', 'Europe - West 4 - B'),
                    ('asia-northeast1-a', 'Asia - Northeast 1 - A'),
                    ('asia-east1-a', 'Asia - East 1 - A'),
                    ('asia-southeast1-a', 'Asia - Southeast 1 - A'),
                    ('australia-southeast1-a', 'Australia Southeast 1 - A')
                ],
                'validators': {
                    'required': True
                }
            },
            'machine_type': {
                'type': 'select',
                'label': 'Machine Type',
                'choices': [
                    ('n1-standard-1', 'Standart: 1 vCPU, 3.75 GB RAM'),
                    ('n1-standard-2', 'Standart: 2 vCPU, 7.5 GB RAM'),
                    ('n1-standard-4', 'Standart: 4 vCPU, 15 GB RAM'),
                    ('n1-standard-8', 'Standart: 8 vCPU, 30 GB RAM'),
                    ('n1-standard-16', 'Standart: 16 vCPU, 60 GB RAM'),
                    ('n1-standard-32', 'Standart: 32 vCPU, 120 GB RAM'),
                    ('n1-standard-64', 'Standart: 64 vCPU, 240 GB RAM')
                ],
                'validators': {
                    'required': True
                }
            }
        }
    }

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """
        # Call parent init to save cluster on self
        super(GceEngine, self).__init__(cluster, **kwargs)
        # Client initialization
        self.service_account_info = kwargs.get('service_account_info', {})
        self.project = self.service_account_info.get('project_id', '')
        self.zone = kwargs.get('zone', '-')
        self.cluster_id = 'a' + self.cluster.id.replace('-', '')
        self.cluster_config = {
            'cluster': {
                'name': self.cluster_id,
                'initialNodeCount': kwargs.get('node_count', 1),
                'nodeConfig': {
                    'machineType': kwargs.get('machine_type', 'n1-standard-1')
                }
            }
        }
        self.client = self._get_client()
        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_client(self):
        """
        Initialize Google client
        Construct service account credentials using the service account key file

        """
        credentials = service_account.Credentials.from_service_account_info(self.service_account_info)
        client = googleapiclient.discovery.build('container', 'v1', credentials=credentials)

        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        try:
            self.client.projects().zones().clusters().create(projectId=self.project, zone=self.zone, body=self.cluster_config).execute()
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason:'.format(self.cluster_id)
            logger.exception(msg)
            return False, msg

        return True, None

    def deprovision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        # test if cluster is considered deprovisioned by the base method
        result, error = super(GceEngine, self).deprovision(**kwargs)
        if result:
            return result, error

        try:
            self.client.projects().zones().clusters().delete(projectId=self.project, zone=self.zone, clusterId=self.cluster_id).execute()
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with following reason: {}'.format(self.cluster_id, repr(e))
            logger.exception(msg)
            return False, msg

        return True, None

    def resize(self, node_count, **kwargs):
        request = self.client.projects().zones().clusters().nodePools().setSize(
            nodePoolId='default-pool',
            clusterId=self.cluster_id,
            zone=self.zone,
            body={'nodeCount': node_count},
            projectId=self.project
        )
        try:
            request.execute()
        except Exception as e:
            msg = 'Resizing cluster {} failed with following reason: {}'.format(self.cluster_id, repr(e))
            logger.exception(msg)
            return False, msg

        self.cluster.metadata['node_count'] = node_count
        self.cluster.save()

        return True, None

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        if not self.cluster.kubeconfig:
            cluster = self.client.projects().zones().clusters().get(projectId=self.project, zone=self.zone, clusterId=self.cluster_id).execute()

            kubeconfig = {}

            if cluster["status"] != "RUNNING":
                return self.cluster.kubeconfig

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

            self.cluster.kubeconfig = kubeconfig
            self.cluster.save()

        return self.cluster.kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        First we try to get cluster by external_id, because its much more efficient in this
        implementation. If its not possible yet, we return from the slower method
        """
        request = self.client.projects().zones().clusters().get(
            projectId=self.project,
            zone=self.zone,
            clusterId=self.cluster_id
        )

        try:
            response = request.execute()
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with following reason: {}'.format(self.cluster_id, repr(e))
            logger.exception(msg)
            return {}

        state = STATE_MAP.get(response['status'], config.get('CLUSTER_UNKNOWN_STATE'))

        key = 'cluster-{}-{}'.format(self.name, self.cluster_id)
        cluster = {
            'key': key,
            'name': self.cluster_id,
            'id': self.cluster.id,
            'state': state,
            'metadata': {}
        }
        return cluster

    def cluster_list(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_list`

        Get list of all clusters, owned by project, both kqueen managed and others in either the specified zone or all zones
        """

        request = self.client.projects().zones().clusters().list(projectId=self.project, zone=self.zone)
        try:
            response = request.execute()
        except Exception as e:
            msg = 'Fetching data from backend for GCE project {} failed with following reason:'.format(self.project_id)
            logger.exception(msg)
            return []

        clusters = response.get('clusters', [])
        if clusters:
            cl = []
            for cluster in clusters:
                state = STATE_MAP.get(cluster['status'], config.get('CLUSTER_UNKNOWN_STATE'))
                key = 'cluster-{}-{}'.format(cluster['name'], self.cluster_id or None)
                item = {
                    'key': key,
                    'name': self.cluster_id or cluster['name'],
                    'id': self.cluster.id or None,
                    'state': state,
                    'metadata': {
                        'node_config': cluster['nodeConfig'],
                        'current_master_version': cluster['currentMasterVersion'],
                        'zone': cluster['zone']
                    }
                }
                cl.append(item)
                return cl

        return []

    @classmethod
    def engine_status(cls, **kwargs):
        service_account_info = kwargs.get('service_account_info', {})
        project = service_account_info.get('project_id', '')
        project_zone = kwargs.get('zone', '-')
        credentials = service_account.Credentials.from_service_account_info(service_account_info)
        client = googleapiclient.discovery.build('container', 'v1', credentials=credentials)

        test_url = 'https://container.googleapis.com/v1/projects/project/zones/zone/clusters?alt=json'
        headers = {'Accept': 'application/json'}
        response = requests.get(test_url, headers=headers)

        if response.status_code == 401:
            try:
                client.projects().zones().clusters().list(projectId=project, zone=project_zone).execute()
            except Exception as e:
                msg = 'Failed to discover GCE project. Check that credentials is valid. Error:'
                logger.exception(msg)
                return config.get('PROVISIONER_UNKNOWN_STATE')
            status = config.get('PROVISIONER_OK_STATE')
        else:
            status = config.get('PROVISIONER_ERROR_STATE')

        return status
