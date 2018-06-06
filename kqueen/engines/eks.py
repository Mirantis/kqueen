from kqueen.config import current_config
from kqueen.engines.base import BaseEngine
import boto3

import logging
import yaml

logger = logging.getLogger('kqueen_api')
config = current_config()

STATE_MAP = {
    'CREATING': config.get('CLUSTER_PROVISIONING_STATE'),
    'ACTIVE': config.get('CLUSTER_OK_STATE'),
    'DELETING': config.get('CLUSTER_DEPROVISIONING_STATE'),
    'FAILED': config.get('CLUSTER_ERROR_STATE'),
    'UPDATED': config.get('CLUSTER_UPDATING_STATE')
}


class EksEngine(BaseEngine):
    """
    Amazon Elastic Kubernetes Service
    """
    name = 'eks'
    verbose_name = 'Amazon Elastic Kubernetes Service'
    parameter_schema = {
        'provisioner': {
            'aws_access_key': {
                'type': 'text',
                'label': 'AWS Access Key',
                'order': 0,
                'validators': {
                    'required': True
                }
            },
            'aws_secret_key': {
                'type': 'text',
                'label': 'AWS Secret Key',
                'order': 1,
                'validators': {
                    'required': True
                }
            }
        },
        'cluster': {
            'node_count': {
                'type': 'integer',
                'label': 'Node Count',
                'default': 3,
                'validators': {
                    'required': True,
                    'min': 1,
                    'number': True
                }
            },
            'roleArn': {
                'type': 'text',
                'label': 'IAM Role ARN',
                'validators': {
                    'required': True
                }
            },
            'subnetid': {
                'type': 'text',
                'label': 'Subnet Id',
                'validators': {
                    'required': True
                }
            },
            'securitygroupid': {
                'type': 'text',
                'label': 'Security Group Id',
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
        super(EksEngine, self).__init__(cluster, **kwargs)
        # Client initialization
        self.aws_access_key = kwargs.get('aws_access_key', '')
        self.aws_secret_key = kwargs.get('aws_secret_key', '')
        self.client = self._get_client()
        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_client(self):
        """
        Initialize Eks client
        """
        client = boto3.client(
            'eks',
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        # self.name = kwargs.get('name', 'noname')
        try:
            response = self.client.create_cluster(
                name=self.cluster.name,
                roleArn=self.cluster.roleArn,
                resourcesVpcConfig={
                    'subnetIds': [
                        self.cluster.subnetid
                    ],
                    'securityGroupIds': [
                        self.cluster.securitygroupid
                    ]
                }
            )
             
            self.cluster.metadata['endpoint'] = response['cluster']['endpoint']
            self.cluster.metadata['roleArn'] = response['cluster']['roleArn']
            self.cluster.metadata['status'] = response['cluster']['status'] 
            self.cluster.metadata['id'] = response['cluster']['name']
            self.cluster.save()
            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Creating cluster {} failed with the following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, msg
        return True, None

    def deprovision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        # test if cluster is considered deprovisioned by the base method
        result, error = super(EksEngine, self).deprovision(**kwargs)
        if result:
            return result, error
        try:
            self.client.delete_cluster(name=self.cluster.metadata['id'])
            # TODO: check if deprovisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with the following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, msg
        return True, None

    def resize(self, node_count, **kwargs):
        """ Implement Later """
        msg = 'Resizing cluster for Eks engine is disabled'
        return False, msg

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        if not self.cluster.kubeconfig:
            cluster = self.client.describe_cluster(name=self.cluster.metadata['id'])
            kubeconfig = {}
            if cluster['cluster']['status'] != "ACTIVE":
                return self.cluster.kubeconfig
            self.cluster.kubeconfig = yaml.load(open("eks-kubeconfig").read()) 
            self.cluster.kubeconfig["clusters"][0]["cluster"] = {
                "server": cluster['endpoint'], 
                "certificate-authority-data": cluster['certificateAuthority']['data']
            }
            self.cluster.kubeconfig["users"][0]["user"]["exec"]["args"][2] = cluster['name']
            self.cluster.save()
        return self.cluster.kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`
        """
        response = {}
        try:
            response = self.client.describe_cluster(self.cluster.metadata['id'])
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with the following reason:'.format(self.cluster.metadata['heat_cluster_id'])
            logger.exception(msg)
            return {}
        state = STATE_MAP.get(response['cluster']['status'], config.get('CLUSTER_UNKNOWN_STATE'))

        key = 'cluster-{}-{}'.format(response['cluster']['name'], response['cluster']['name'])
        cluster = {
            'key': key,
            'name': response['cluster']['name'],
            'id': response['cluster']['name'],
            'state': state,
            'metadata': self.cluster.metadata
        }
        return cluster

    def cluster_list(self):
        """Is not needed in Eks"""
        return []

    @classmethod
    def engine_status(cls, **kwargs):
        try:
            aws_access_key = kwargs.get('aws_access_key', '')
            aws_secret_key = kwargs.get('aws_secret_key', '')
        except Exception:
            logger.exception('{} Eks Provisioner validation failed.'.format(cls.name))
            return config.get('PROVISIONER_ERROR_STATE')
        client = boto3.client(
            'eks',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        try:
            list(client.list_clusters())
        except Exception:
            logger.exception('{} Eks Provisioner validation failed.'.format(cls.name))
            return config.get('PROVISIONER_UNKNOWN_STATE')
        return config.get('PROVISIONER_OK_STATE')
