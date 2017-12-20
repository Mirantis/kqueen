from kqueen.config import current_config
from kqueen.engines.base import BaseEngine

from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.containerservice import ContainerServiceClient

import logging
import base64
import yaml

logger = logging.getLogger(__name__)
config = current_config()

STATE_MAP = {
    'Creating': config.get('CLUSTER_PROVISIONING_STATE'),
    'Succeeded': config.get('CLUSTER_OK_STATE'),
    'Deleting': config.get('CLUSTER_DEPROVISIONING_STATE'),
    'Failed': config.get('CLUSTER_ERROR_STATE')
}


class AksEngine(BaseEngine):
    """
    Azure Container Service
    """
    name = 'aks'
    verbose_name = 'Azure Kubernetes Managed Service'
    resource_group_name = 'test-cluster'
    parameter_schema = {
        'provisioner': {
            'client_id': {
                'type': 'text',
                'label': 'Client ID',
                'validators': {
                    'required': True
                }
            },
            'secret': {
                'type': 'password',
                'label': 'Secret',
                'validators': {
                    'required': True
                }
            },
            'tenant': {
                'type': 'text',
                'label': 'Tenant',
                'validators': {
                    'required': True
                }
            },
            'subscription_id': {
                'type': 'text',
                'label': 'Subscription ID',
                'validators': {
                    'required': True
                }
            },
        },
        'cluster': {
            'location': {
                'type': 'select',
                'label': 'Location',
                'choices': [
                    ('eastus', 'East US'),
                    ('centralus', 'Central US'),
                    ('westeurope', 'West Europe')
                ],
                'validators': {
                    'required': True
                }
            },
            'ssh_key': {
                'type': 'text_area',
                'label': 'SSH Key (public)',
                'validators': {}
            },
            'node_count': {
                'type': 'integer',
                'label': 'Node Count',
                'default': 1,
                'validators': {
                    'required': True,
                    'min': 1,
                    'number': True
                }
            }
        }
    }

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """
        # Call parent init to save cluster on self
        super(AksEngine, self).__init__(cluster, **kwargs)

        # Client initialization
        self.client_id = kwargs.get('client_id', '')
        self.secret = kwargs.get('secret', '')
        self.tenant = kwargs.get('tenant', '')
        self.subscription_id = kwargs.get('subscription_id', '')
        self.resource_group_name = kwargs.get('resource_group_name', self.resource_group_name)
        self.location = kwargs.get('location', '')
        self.ssh_key = kwargs.get('ssh_key', '')
        self.node_count = kwargs.get('node_count', 1)
        self.client = self._get_client()

        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_client(self):
        """
        Initialize Azure client
        Construct service account credentials using the service account key file

        """
        credentials = ServicePrincipalCredentials(client_id=self.client_id, secret=self.secret, tenant=self.tenant)
        subscription_id = self.subscription_id
        client = ContainerServiceClient(credentials, subscription_id)

        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        cluster = {
            'location': self.location,
            'type': 'Microsoft.ContainerService/ManagedClusters',
            'name': self.cluster.id,
            'properties': {
                # TODO: fix hardcoded params
                'kubernetes_version': '1.7.7',
                'dns_prefix': 'test-cluster',
                'agent_pool_profiles': [
                    {
                        'fqdn': None,
                        'vnet_subnet_id': None,
                        'storage_profile': 'ManagedDisks',
                        'name': 'agentpool',
                        'count': self.node_count,
                        'dns_prefix': None,
                        'ports': None,
                        'vm_size': 'Standard_D2_v2',
                        'os_type': 'Linux',
                        'os_disk_size_gb': None
                    }
                ],
                'service_principal_profile': {
                    'client_id': self.client_id,
                    'secret': self.secret
                },
                'linux_profile': {
                    'admin_username': 'azureuser',
                    'ssh': {
                        'public_keys': [
                            {
                                'key_data': self.ssh_key
                            }
                        ]
                    }
                }
            }
        }

        try:
            self.client.managed_clusters.create_or_update(self.resource_group_name, self.cluster.id, cluster)
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason: {}'.format(self.cluster.id, repr(e))
            logger.error(msg)
            return False, msg

        return True, None

    def deprovision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        try:
            self.client.managed_clusters.delete(self.resource_group_name, self.cluster.id)
            # TODO: check if deprovisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with following reason: {}'.format(self.cluster.id, repr(e))
            logger.error(msg)
            return False, msg

        return True, None

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        if not self.cluster.kubeconfig:
            cluster = self.client.managed_clusters.get(self.resource_group_name, self.cluster.id)

            kubeconfig = {}

            if cluster.properties.provisioning_state != "Succeeded":
                return self.cluster.kubeconfig

            access_profiles = cluster.properties.access_profiles.as_dict()
            access_profile = access_profiles.get('cluster_admin')
            encoded_kubeconfig = access_profile.get("kube_config")
            kubeconfig = base64.b64decode(encoded_kubeconfig).decode(encoding='UTF-8')

            self.cluster.kubeconfig = yaml.load(kubeconfig)
            self.cluster.save()

        return self.cluster.kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        First we try to get cluster by external_id, because its much more efficient in this
        implementation. If its not possible yet, we return from the slower method
        """
        try:
            response = self.client.managed_clusters.get(self.resource_group_name, self.cluster.id)
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with following reason: {}'.format(self.cluster.id, repr(e))
            logger.error(msg)
            return {}
        properties = response.properties.as_dict()
        state = STATE_MAP.get(properties.get('provisioning_state'), config.get('CLUSTER_UNKNOWN_STATE'))

        key = 'cluster-{}-{}'.format(self.name, self.cluster.id)
        cluster = {
            'key': key,
            'name': self.cluster.id,
            'id': self.cluster.id,
            'state': state,
            'metadata': {}
        }
        return cluster

    def cluster_list(self):
        """AKS engine don't support list of clusters"""
        # TODO: it does, add list of clusters

        return []
