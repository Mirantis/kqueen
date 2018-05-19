from kqueen.config import current_config
from kqueen.engines.base import BaseEngine

from keystoneauth1 import loading
from keystoneauth1 import session
from heatclient import client as hclient
from urllib.request import urlopen

import logging
import yaml

logger = logging.getLogger('kqueen_api')
config = current_config()

# TODO: change to match openstack heat status
STATE_MAP = {
    'CREATE_IN_PROGRESS': config.get('CLUSTER_PROVISIONING_STATE'),
    'CREATE_COMPLETE': config.get('CLUSTER_OK_STATE'),
    'DELETED': config.get('CLUSTER_DEPROVISIONING_STATE'),
    'FAILED': config.get('CLUSTER_ERROR_STATE'),
    'UPDATED': config.get('CLUSTER_UPDATING_STATE')
}


class OpenstackEngine(BaseEngine):
    """
    Openstack Heat Service
    """
    name = 'openstack'
    verbose_name = 'Openstack Heat Service'
    parameter_schema = {
        'provisioner': {
            'os_username': {
                'type': 'text',
                'label': 'User Name',
                'order': 0,
                'validators': {
                    'required': True
                }
            },
            'os_password': {
                'type': 'password',
                'label': 'Password',
                'order': 1,
                'validators': {
                    'required': True
                }
            },
            'os_tenant_name': {
                'type': 'text',
                'label': 'Project/Tenant Name',
                'order': 2,
                'validators': {
                    'required': True
                }
            },
            'os_project_id': {
                'type': 'text',
                'label': 'Project/Tenant ID',
                'order': 3,
                'validators': {
                    'required': True
                }
            },
            'os_user_domain_name': {
                'type': 'text',
                'label': 'User Domain Name',
                'order': 4,
                'validators': {
                    'required': True
                }
            },
            'os_auth_url': {
                'type': 'text',
                'label': 'Authentication URL (keystone)',
                'order': 5,
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
            }
        }
    }

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """
        # Call parent init to save cluster on self
        super(OpenstackEngine, self).__init__(cluster, **kwargs)
        # Client initialization
        self.os_username = kwargs.get('os_username', '')
        self.os_password = kwargs.get('os_password', '')
        self.os_tenant_name = kwargs.get('os_tenant_name', '')
        self.os_auth_url = kwargs.get('os_auth_url', '')
        self.os_user_domain_name = kwargs.get('os_user_domain_name', '')
        self.os_project_id = kwargs.get('os_project_id', '')
        k8stemp = open("/code/prod/openstack/heat-templates/kubernetes-cluster.yaml")
        self.os_heat_k8s_template = yaml.load(k8stemp)
        self.os_heat_k8s_template["heat_template_version"] = "2013-05-23"
        # self.os_heat_k8s_template = kwargs.get('os_heat_k8s_template', '')
        self.client = self._get_client()
        # Cache settings
        self.cache_timeout = 5 * 60

    def _get_client(self):
        """
        Initialize Openstack Heat client
        """
        loader = loading.get_plugin_loader('password')
        auth = loader.load_from_options(auth_url=self.os_auth_url,
                                        username=self.os_username,
                                        password=self.os_password,
                                        project_id=self.os_project_id,
                                        user_domain_name=self.os_user_domain_name,
                                        project_name=self.os_tenant_name)
        sess = session.Session(auth=auth)
        client = hclient.Client('1', session=sess)
        return client

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        # self.name = kwargs.get('name', 'noname')
        try:
            response = self.client.stacks.create(files={}, disable_rollback=True, stack_name=self.cluster.name, template=self.os_heat_k8s_template)
            self.cluster.metadata['heat_cluster_id'] = response['stack']['id']
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
        result, error = super(OpenstackEngine, self).deprovision(**kwargs)
        if result:
            return result, error
        try:
            self.client.stacks.delete(self.cluster.metadata['heat_cluster_id'])
            # TODO: check if deprovisioning response is healthy
        except Exception as e:
            msg = 'Deleting cluster {} failed with the following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, msg
        return True, None

    def resize(self, node_count, **kwargs):
        """ Implement Later """
        msg = 'Resizing cluster for Openstack engine is disabled'
        return False, msg
        # try:
        # self.client.stacks.update(stack_id, data)
        # TODO: check if resizing response is healthy
        # except Exception as e:
        # msg = 'Resizing cluster {} failed with the following reason:'.format(self.cluster.id)
        # logger.exception(msg)
        # return False, msg
        # self.cluster.metadata['node_count'] = node_count
        # self.cluster.save()
        # return True, None

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        if not self.cluster.kubeconfig:
            cluster = self.client.stacks.get(self.cluster.metadata['heat_cluster_id'])
            kubeconfig = {}
            if cluster.stack_status != "CREATE_COMPLETE":
                return self.cluster.kubeconfig
            response = self.client.stacks.output_show(self.cluster.metadata['heat_cluster_id'], "kubeconfig")
            conf = urlopen(response['output']['output_value'])
            response2 = self.client.stacks.output_show(self.cluster.metadata['heat_cluster_id'], "instance1_public_ip")
            publicip = response2['output']['output_value']
            kubeconfig = conf.read()
            self.cluster.kubeconfig = yaml.load(kubeconfig)
            self.cluster.kubeconfig["clusters"][0]["cluster"] = {"insecure-skip-tls-verify": True, "server": "https://" + publicip + ":6443"}
            self.cluster.save()
        return self.cluster.kubeconfig

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`
        """
        response = {}
        try:
            response = self.client.stacks.get(self.cluster.metadata['heat_cluster_id'])
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with the following reason:'.format(self.cluster.metadata['heat_cluster_id'])
            logger.exception(msg)
            return {}
        state = STATE_MAP.get(response.stack_status, config.get('CLUSTER_UNKNOWN_STATE'))

        key = 'cluster-{}-{}'.format(response.stack_name, response.id)
        cluster = {
            'key': key,
            'name': response.stack_name,
            'id': response.id,
            'state': state,
            'metadata': self.cluster.metadata
        }
        return cluster

    def cluster_list(self):
        """Is not needed in Heat"""
        return []

    @classmethod
    def engine_status(cls, **kwargs):
        try:
            loader = loading.get_plugin_loader('password')
            os_username = kwargs.get('os_username', '')
            os_password = kwargs.get('os_password', '')
            os_auth_url = kwargs.get('os_auth_url', '')
            os_project_name = kwargs.get('os_tenant_name', '')
            os_project_id = kwargs.get('os_project_id', '')
            os_user_domain_name = kwargs.get('os_user_domain_name', '')
            auth = loader.load_from_options(auth_url=os_auth_url,
                                            username=os_username,
                                            password=os_password,
                                            project_id=os_project_id,
                                            user_domain_name=os_user_domain_name,
                                            project_name=os_project_name)
            sess = session.Session(auth=auth)
        except Exception:
            logger.exception('{} Openstack Provisioner validation failed.'.format(cls.name))
            return config.get('PROVISIONER_ERROR_STATE')
        client = hclient.Client('1', session=sess)
        try:
            list(client.stacks.list())
        except Exception:
            logger.exception('{} Openstack Provisioner validation failed.'.format(cls.name))
            return config.get('PROVISIONER_UNKNOWN_STATE')
        return config.get('PROVISIONER_OK_STATE')
