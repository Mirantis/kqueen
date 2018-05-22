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
    'RECONCILING': config.get('CLUSTER_UPDATING_STATE'),
    'ERROR': config.get('CLUSTER_ERROR_STATE')
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
                'order': 0,
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
                'order': 1,
                'default': 1,
                'class_name': 'gke_node_count',
                'validators': {
                    'required': True,
                    'min': 1,
                    'number': True
                }
            },
            'zone': {
                'type': 'select',
                'label': 'Zone',
                'order': 2,
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
                'order': 3,
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
            },
            'network_range': {
                'type': 'text',
                'label': 'Network range CIDR',
                'order': 4,
                'placeholder': '10.0.0.0/14',
                'validators': {
                    'required': False,
                    'cidr': True
                }
            },
            'network_policy': {
                'type': 'select',
                'label': 'Network Policy',
                'order': 5,
                'choices': [
                    ('PROVIDER_UNSPECIFIED', '<disabled>'),
                    ('CALICO', 'Calico')
                ],
                'default': 'PROVIDER_UNSPECIFIED',
                'validators': {
                    'required': False
                },
                'class_name': 'network-policy'
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

        # Generate metadata for Network Policies if empty
        if not isinstance(cluster.metadata.get('network_policy'), dict):
            network_provider = kwargs.get('network_policy', 'PROVIDER_UNSPECIFIED')
            self.cluster.metadata['network_policy'] = {
                'provider': network_provider,
                'enabled': network_provider != 'PROVIDER_UNSPECIFIED'
            }
            logger.debug('Generate metadata for network policies: {}'
                         .format(self.cluster.metadata['network_policy']))
            self.cluster.save()

        meta = self.cluster.metadata
        self.cluster_config = {
            'cluster': {
                'name': self.cluster_id,
                'initialNodeCount': kwargs.get('node_count', 1),
                'nodeConfig': {
                    'machineType': kwargs.get('machine_type', 'n1-standard-1')
                },
                'addonsConfig': {
                    'networkPolicyConfig': {
                        'disabled': meta['network_policy'].get('provider', 'PROVIDER_UNSPECIFIED') == 'PROVIDER_UNSPECIFIED'
                    }
                },
                'clusterIpv4Cidr': kwargs.get('network_range', ''),
                'networkPolicy': {
                    'provider': meta['network_policy'].get('provider', 'PROVIDER_UNSPECIFIED'),
                    'enabled': meta['network_policy'].get('enabled', False)
                }
            }
        }

        logger.debug('GKE cluster configuration: {}'.format(self.cluster_config))
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

        request = self.client.projects().zones().clusters().create(projectId=self.project,
                                                                   zone=self.zone,
                                                                   body=self.cluster_config)
        cluster_config = self.cluster_config['cluster']
        network_meta = self.cluster.metadata['network_policy']
        if network_meta['provider'] == 'CALICO' and int(cluster_config['initialNodeCount']) < 2:
            msg = 'Setting {} Network Policy for the cluster {} denied due to '\
                  'unsupported configuration. The minimal size of the '\
                  'cluster to run network policy enforcement is 2 '\
                  'n1-standard-1 instances'.format(network_meta['provider'],
                                                   self.cluster_id)
            logger.error(msg)
            return False, msg
        try:
            request.execute()
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Creating cluster {} failed with the following reason: {}'.format(self.cluster_id, e)
            logger.exception(msg)
            return False, e

        if cluster_config['networkPolicy']['provider'] != 'PROVIDER_UNSPECIFIED':
            network_meta['provider'] = cluster_config['networkPolicy']['provider']
            network_meta['enabled'] = cluster_config['networkPolicy']['enabled']
            logger.debug('Provisioning cluster {} started, updating metadata...{}'
                         .format(self.cluster_id, self.cluster.metadata))
            self.cluster.save()

        return True, None

    def deprovision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        # test if cluster is considered deprovisioned by the base method
        result, error = super(GceEngine, self).deprovision(**kwargs)
        if result:
            return result, error
        request = self.client.projects().zones().clusters().delete(projectId=self.project,
                                                                   zone=self.zone,
                                                                   clusterId=self.cluster_id)
        try:
            request.execute()
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with following reason: {}'.format(self.cluster_id,
                                                                                repr(e))
            logger.exception(msg)
            return False, msg

        return True, None

    def resize(self, node_count, **kwargs):

        if int(node_count) < 2 and \
           self.cluster_config['cluster']['networkPolicy']['enabled'] is True:
            msg = 'Resizing cluster {} denied. The minimum size cluster to run \
                   network policy enforcement is 2 n1-standard-1 instances.\
                   Otherwise, turn off network policy before resizing.'\
                   .format(self.cluster_id)
            logger.error(msg)
            return False, msg

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
            msg = 'Resizing cluster {} failed with the following reason: {}'\
                  .format(self.cluster_id, repr(e))
            logger.exception(msg)
            return False, msg

        self.cluster.metadata['node_count'] = node_count
        self.cluster.save()

        return True, None

    def set_network_policy(self, network_provider='CALICO', enabled=False, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        unsupported_instances = ['g1-small', 'f1-micro']
        network_policy_body = {
            'networkPolicy': {
                'provider': network_provider,
                'enabled': enabled
            }
        }

        m_type = self.cluster_config['cluster']['nodeConfig']['machineType']
        current_node_count = int(self.cluster_config['cluster'].get('initialNodeCount', 1))

        if current_node_count < 2 or m_type in unsupported_instances:
            msg = 'Setting {} Network Policy for the cluster {} denied due to \
                   unsupported configuration. The recommended minimum size \
                   cluster to run network policy enforcement is 3 \
                   n1-standard-1 instances'.format(network_provider,
                                                   self.cluster_id)
            logger.error(msg)
            return False, msg

        logger.debug('Required Node amount for Network Policy is 2, current node amount: {}'
                     .format(current_node_count))
        network_addon = self.cluster_config['cluster']['addonsConfig'].get('networkPolicyConfig',
                                                                           {})
        logger.debug('Enabled Network addon: {}'.format(network_addon))

        if network_addon.get('disabled', True) is True:
            msg = 'Setting {} Network Policy for the cluster {} denied due to \
                   disabled Network Policy addon. Recreate stack with enabled \
                   Network Policy'.format(network_provider, self.cluster_id)
            logger.error(msg)
            return False, msg

        logger.debug('Setting {} network policy to cluster {}...'.format(network_provider,
                                                                         self.cluster_id))
        request = self.client.projects().zones().clusters().setNetworkPolicy(
            projectId=self.project, zone=self.zone,
            clusterId=self.cluster_id, body=network_policy_body)

        try:
            request.execute()
        except Exception as e:
            msg = 'Setting {} Network Policy for cluster {} failed with the following reason: {}'\
                .format(network_provider, self.cluster_id, e)
            logger.exception(msg)
            return False, msg

        logger.debug('Setting {} network policy to cluster {} passed successfully,\
                     saving metadata...'.format(network_provider, self.cluster_id))

        meta = self.cluster.metadata.get('network_policy', {})
        meta['provider'] = network_provider
        meta['enabled'] = enabled
        logger.debug('Updating network policy for cluster {} started, saving metadata...{}'
                     .format(self.cluster_id, self.cluster.metadata['network_policy']))
        self.cluster.save()

        return True, None

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        if not self.cluster.kubeconfig:
            request = self.client.projects().zones().clusters().get(projectId=self.project,
                                                                    zone=self.zone,
                                                                    clusterId=self.cluster_id)
            cluster = request.execute()

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
            msg = 'Fetching data from backend for cluster {} failed with the following reason: {}'\
                .format(self.cluster_id, repr(e))
            logger.exception(msg)
            return {}

        state = STATE_MAP.get(response['status'], config.get('CLUSTER_UNKNOWN_STATE'))

        key = 'cluster-{}-{}'.format(self.name, self.cluster_id)
        cluster = {
            'key': key,
            'name': self.cluster_id,
            'id': self.cluster.id,
            'state': state,
            'metadata': {'status_message': response['statusMessage']} if 'statusMessage' in response else {}
        }
        return cluster

    def cluster_list(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_list`

        Get list of all clusters, owned by project,
        both kqueen managed and others in either the specified zone or all zones
        """

        request = self.client.projects().zones().clusters().list(projectId=self.project,
                                                                 zone=self.zone)
        try:
            response = request.execute()
        except Exception as e:
            msg = 'Fetching data from backend for GCE project {} failed with the following reason:'\
                .format(self.project_id)
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
            request = client.projects().zones().clusters().list(projectId=project, zone=project_zone)
            try:
                request.execute()
            except Exception as e:
                msg = 'Failed to discover GCE project. Check that credentials is valid. Error:'
                logger.exception(msg)
                return config.get('PROVISIONER_UNKNOWN_STATE')
            status = config.get('PROVISIONER_OK_STATE')
        else:
            status = config.get('PROVISIONER_ERROR_STATE')

        return status
