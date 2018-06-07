from kqueen.config import current_config
from kqueen.engines.base import BaseEngine
import boto3

import logging
import pkgutil
import yaml

logger = logging.getLogger('kqueen_api')
config = current_config()

STATE_MAP = {
    'CREATING': config.get('CLUSTER_PROVISIONING_STATE'),
    'ACTIVE': config.get('CLUSTER_OK_STATE'),
    'DELETING': config.get('CLUSTER_DEPROVISIONING_STATE'),
    'FAILED': config.get('CLUSTER_ERROR_STATE'),
    'UPDATING': config.get('CLUSTER_UPDATING_STATE')
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
            },
            'aws_region': {
                'type': 'select',
                'label': 'AWS Region',
                'order': 2,
                'choices': [
                    ('us-east-1', 'US East (N. Virginia)'),
                    ('us-east-2', 'US East (Ohio)'),
                    ('us-west-1', 'US West (N. California)'),
                    ('us-west-2', 'US West (Oregon)'),
                    ('ca-central-1', 'Canada (Central)'),
                    ('eu-central-1', 'EU (Frankfurt)'),
                    ('eu-west-1', 'EU (Ireland)'),
                    ('eu-west-2', 'EU (London)'),
                    ('eu-west-3', 'EU (Paris)'),
                    ('ap-northeast-1', 'Asia Pacific (Tokyo)'),
                    ('ap-northeast-2', 'Asia Pacific (Seoul)'),
                    ('ap-northeast-3', 'Asia Pacific (Osaka-Local)'),
                    ('ap-southeast-1', 'Asia Pacific (Singapore)'),
                    ('ap-southeast-2', 'Asia Pacific (Sydney)'),
                    ('ap-south-1', 'Asia Pacific (Mumbai)'),
                    ('sa-east-1', 'South America (São Paulo)')
                ],
                'validators': {
                    'required': True
                }
            }
        },
        'cluster': {
            'node_count': {
            # TODO unsupported, need to define template k8s input
                'type': 'integer',
                'label': 'Node Count',
                'default': 3,
                'order': 3,
                'validators': {
                    'required': True,
                    'min': 1,
                    'number': True
                }
            },
            'role_arn': {
                'type': 'text',
                'label': 'IAM Role ARN',
                'order': 4,
                'validators': {
                    'required': True
                }
            },
            'subnet_id': {
            # TODO subnetIds list - Amazon EKS requires subnets in at least two Availability Zones.
            # TODO subnetIds must be attached to common security-group.
                'type': 'text',
                'label': 'Subnet Id',
                'order': 5,
                'validators': {
                    'required': True
                }
            },
            'security_group_id': {
            # TODO securityGroupIds (list) -- Specify one or more security groups
                'type': 'text',
                'label': 'Security Group Id',
                'order': 6,
                'validators': {
                    'required': False
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
        self.aws_access_key = kwargs['aws_access_key']
        self.aws_secret_key = kwargs['aws_secret_key']
        self.aws_region = kwargs['aws_region']
        self.client = self._get_client()
        # Cluster settings
        self.role_arn = kwargs['role_arn']
        subnets = kwargs['subnet_id']
        self.subnet_id = subnets.split(',').strip()
        security_groups = kwargs.get('security_group_id', '')
        self.security_group_id = security_groups.split(',').strip()
        # Get templates
        files = self._get_template_files()
        self.eks_kubeconfig = files['template.yaml']
        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_template_files(self):
        package_name = "kqueen.engines.resources.aws"
        files = {}
        entities = ['template']
        for f in entities:
            files[f + ".yaml"] = pkgutil.get_data(package_name, f + ".yaml")
        return files

    def _get_client(self):
        """
        Initialize Eks client
        """
        client = boto3.client(
            'eks',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
        )
        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        try:
            response = self.client.create_cluster(
                name=self.cluster.id,
                roleArn=self.role_arn,
                resourcesVpcConfig={
                    'subnetIds': self.subnet_id,
                    'securityGroupIds': self.security_group_id
                }
            )

            # TODO: check if provisioning response is healthy
        except Exception as e:
            msg = 'Creating cluster {} failed with the following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, e
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
            self.client.delete_cluster(name=self.cluster.id)
            # TODO: check if deprovisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with the following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, e
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
            cluster = self.client.describe_cluster(name=self.cluster.id)
            kubeconfig = {}
            if cluster['cluster']['status'] != "ACTIVE":
                return self.cluster.kubeconfig
            self.cluster.kubeconfig = yaml.load(self.eks_kubeconfig)
            self.cluster.kubeconfig["clusters"][0]["cluster"] = {
                "server": cluster['cluster']['endpoint'],
                "certificate-authority-data": cluster['cluster']['certificateAuthority']['data']
            }
            self.cluster.kubeconfig["users"][0]["user"]["exec"]["args"][2] = cluster['cluster']['name']
            # TODO define , do we need to use user Arn or Cluster Arn
#            self.cluster.kubeconfig["users"][0]["user"]["exec"]["args"][4] = cluster['cluster']['roleArn']
#            self.cluster.kubeconfig["users"][0]["user"]["exec"]["args"][4] = cluster['cluster']['arn']
            self.cluster.save()
        return self.cluster.kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`
        """
        response = {}
        try:
            response = self.client.describe_cluster(name=self.cluster.id)
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with the following reason:'.format(self.cluster.id)
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
            aws_access_key = kwargs['aws_access_key']
            aws_secret_key = kwargs['aws_secret_key']
            aws_region = kwargs['aws_region']
        except KeyError:
            return config.get('PROVISIONER_ERROR_STATE')

        client = boto3.client(
            'eks',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )
        try:
            list(client.list_clusters())
        except Exception:
            logger.exception('{} Eks Provisioner validation failed.'.format(cls.name))
            return config.get('PROVISIONER_UNKNOWN_STATE')

        return config.get('PROVISIONER_OK_STATE')
