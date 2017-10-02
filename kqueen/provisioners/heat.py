from werkzeug.contrib.cache import SimpleCache

import logging

import keystoneclient
from keystoneauth1.identity import v2
from keystoneauth1.identity import v3
from keystoneauth1 import session
import heatclient
import heatclient.client


logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cache = SimpleCache()


class HeatProvisioner():
    def __init__(self, *args, **kwargs):
        # Get keystone version
        keystone_cli = keystoneclient.client.Client(endpoint=kwargs.get('auth_url'))

        # Auth for different versions
        if keystone_cli.version == "v2":
            auth = v2.Password(
                auth_url=kwargs.get("auth_url", ""),
                username=kwargs.get('username', ""),
                password=kwargs.get('password', ""),
                user_id=kwargs.get("user_id", ""),
                trust_id=kwargs.get('trust_id', ""),
                tenant_id=kwargs.get('tenant_id', ""),
                tenant_name=kwargs.get('tenant_id', ""),
                reauthenticate=kwargs.get("reauthenticate", False))
        elif keystone_cli.version == "v3":
            auth = v3.Password(
                auth_url=kwargs.get("auth_url", ""),
                password=kwargs.get("password", ""),
                username=kwargs.get("username", ""),
                user_id=kwargs.get("user_id", ""),
                user_domain_id=kwargs.get("user_domain_id", ""),
                user_domain_name=kwargs.get("user_domain_name", ""),
                trust_id=kwargs.get('trust_id', ""),
                domain_id=kwargs.get("domain_id", ""),
                domain_name=kwargs.get("domain_name", ""),
                project_id=kwargs.get("project_id", ""),
                project_name=kwargs.get("project_name", ""),
                project_domain_id=kwargs.get("project_domain_id", ""),
                project_domain_name=kwargs.get("project_domain_name", ""),
                reauthenticate=kwargs.get("reauthenticate", False))

        sess = session.Session(auth=auth)
        self.heat_cli = heatclient.client.Client('1', session=sess)

        self.provisioner = "heat"
        self.cache_timeout = 5 * 60

        self.stack_name = kwargs.get("stack_name")

    def get_stack(self):
        self.stack = self.heat_cli.stacks.get(self.stack_name)

    def list(self):
        clusters = {}
        cluster_id = 'cluster-{}-{}'.format(self.provisioner, self.stack_name)
        clusters[cluster_id] == cache.get(cluster_id)

        if clusters[cluster_id] is None:
            logger.debug('Stack {} missing in cache'.format(cluster_id))
            try:
                self.get_stack()

                outputs = {}
                for output in self.stack.outputs:
                    outputs[output['output_key']] = output['output_value']

                clusters[cluster_id] = {
                    'name': self.stack_name,
                    'state': self.stack.status,
                    'outputs': outputs
                }
            except heatclient.exc.HTTPNotFound:
                logger.debug('Stack {} not found'.format(self.stack_name))
                clusters[cluster_id] = {
                    'name': self.stack_name,
                    'state': 'NOT_FOUND',
                    'outputs': {}
                }
            cache.set(cluster_id, clusters[cluster_id], timeout=self.cache_timeout)

        return clusters
