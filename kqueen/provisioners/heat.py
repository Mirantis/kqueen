import keystoneclient
from keystoneauth1 import session
from keystoneauth1.identity import v2
from keystoneauth1.identity import v3

import heatclient
import heatclient.client
from heatclient.common import template_utils

import logging
from werkzeug.contrib.cache import SimpleCache

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cache = SimpleCache()


class HeatProvisioner():

    def __init__(self, clusters=[], *args, **kwargs):
        self.provisioner = 'heat'
        self.cache_timeout = kwargs.get('cache_timeout', 5 * 60)

        self.__cli_setup(*args, **kwargs)

        self.clusters = {}
        self.__import_clusters(clusters)

    def __cli_setup(self, *args, **kwargs):
        # Get keystone version
        keystone_cli = keystoneclient.client.Client(endpoint=kwargs.get('auth_url'))

        # Auth for different versions
        if keystone_cli.version == 'v2':
            auth = v2.Password(
                auth_url=kwargs.get('auth_url', ''),
                username=kwargs.get('username', ''),
                password=kwargs.get('password', ''),
                user_id=kwargs.get('user_id', ''),
                trust_id=kwargs.get('trust_id', ''),
                tenant_id=kwargs.get('tenant_id', ''),
                tenant_name=kwargs.get('tenant_id', ''),
                reauthenticate=kwargs.get('reauthenticate', False))
        elif keystone_cli.version == 'v3':
            auth = v3.Password(
                auth_url=kwargs.get('auth_url', ''),
                password=kwargs.get('password', ''),
                username=kwargs.get('username', ''),
                user_id=kwargs.get('user_id', ''),
                user_domain_id=kwargs.get('user_domain_id', ''),
                user_domain_name=kwargs.get('user_domain_name', ''),
                trust_id=kwargs.get('trust_id', ''),
                domain_id=kwargs.get('domain_id', ''),
                domain_name=kwargs.get('domain_name', ''),
                project_id=kwargs.get('project_id', ''),
                project_name=kwargs.get('project_name', ''),
                project_domain_id=kwargs.get('project_domain_id', ''),
                project_domain_name=kwargs.get('project_domain_name', ''),
                reauthenticate=kwargs.get('reauthenticate', False))

        sess = session.Session(auth=auth)
        self.heat_cli = heatclient.client.Client('1', session=sess)

    def __import_clusters(self, clusters):
        for cluster in clusters:
            self.clusters[cluster.id] = cluster

    def __process_required_files(self, template_file, env_paths):
        merged_files, merged_env = template_utils.process_multiple_environments_and_files(env_paths)
        composite_templates, template = template_utils.process_template_path(template_file)
        merged_files.update(composite_templates)
        return template, merged_files, merged_env

    def __get_stack(self, stack_id):
        return self.heat_cli.stacks.get(stack_id)

    def __create_stack(self, stack_name, template, files, environment):
        return self.heat_cli.stacks.create(stack_name=stack_name, template=template, files=files, environment=environment)

    def __delete_stack(self, stack_id):
        return self.heat_cli.stacks.delete(stack_id=stack_id)

    def create(self, stack_name, template_file, env_paths=[]):
        cluster_id = 'cluster-{}-{}'.format(self.provisioner, stack_name)

        if cluster_id not in self.clusters:
            # Load all required files for template
            template, merged_files, merged_env = self.__process_required_files(template_file, env_paths)

            try:
                # Create stack
                r = self.__create_stack(stack_name, template, merged_files, merged_env)
            except Exception as e:
                logger.error('Stack {} failed to create with reason: {}'.format(stack_name, str(e)))
                return None

            self.clusters[cluster_id] = {
                'name': cluster_id,
                'provisioner': self.provisioner,
                'state': 'CREATE_IN_PROGRESS',
                'parameters': {
                    'stack_id': r['stack']['id'],
                    'outputs': {},
                },
                'kubeconfig': ''
            }
        else:
            logger.error('Stack {} already exists. Create aborted'.format(stack_name))

        return self.clusters[cluster_id]

    def get(self, cluster_id, cacheEnabled=True, kubeconfig_output_key='kubeconfig'):
        if cacheEnabled and cache.get(cluster_id):
            return cache.get(cluster_id)

        if cluster_id in self.clusters:
            stack_id = self.clusters[cluster_id]['parameters']['stack_id']
            try:
                stack = self.__get_stack(stack_id)
                logger.debug('Stack {} found'.format(stack_id))

                outputs = {}
                for output in stack.outputs:
                    outputs[output['output_key']] = output['output_value']

                self.clusters[cluster_id]['state'] = stack.status
                self.clusters[cluster_id]['parameters']['outputs'] = outputs
                if kubeconfig_output_key in outputs:
                    self.clusters[cluster_id]['kubeconfig'] = outputs[kubeconfig_output_key]

                cache.set(cluster_id, self.clusters[cluster_id], timeout=self.cache_timeout)
            except heatclient.exc.HTTPNotFound:
                if self.clusters[cluster_id]['state'] == 'DELETE_IN_PROGRESS':
                    logger.info('Stack {} was succesfully deleted'.format(stack_id))
                else:
                    logger.error('Stack {} not found. Local DB is out of sync with target. Removing cluster: {} from local DB '.format(stack_id, cluster_id))
                self.clusters.pop(cluster_id)
                cache.delete(cluster_id)
                return None
        else:
            logger.error('Cluster {} not managed by this provisioner'.format(cluster_id))
            return None

        return self.clusters[cluster_id]

    def get_kubeconfig(self, cluster_id, cacheEnabled=True, kubeconfig_output_key='kubeconfig'):
        if cacheEnabled and cache.get(cluster_id):
            return cache.get(cluster_id)['kubeconfig']

        return self.get(cluster_id, cacheEnabled, kubeconfig_output_key)['kubeconfig']

    def list(self, cacheEnabled=True):
        if not cacheEnabled:
            for cluster_id in self.clusters:
                self.clusters[cluster_id] = self.get(cluster_id, cacheEnabled=False)
        return self.clusters

    def delete(self, cluster_id):
        if cluster_id in self.clusters:
            stack_id = self.clusters[cluster_id]['parameters']['stack_id']
            try:
                self.__delete_stack(stack_id)
                cache.delete(cluster_id)
                self.clusters[cluster_id]['state'] = 'DELETE_IN_PROGRESS'
                return True
            except heatclient.exc.HTTPNotFound:
                if self.clusters[cluster_id]['state'] == 'DELETE_IN_PROGRESS':
                    logger.info('Stack {} was succesfully deleted'.format(stack_id))
                else:
                    logger.error('Stack {} not found. Local DB is out of sync with target. Removing cluster: {} from local DB '.format(stack_id, cluster_id))
                self.clusters.pop(cluster_id)
                cache.delete(cluster_id)
                return True
            except Exception as e:
                logger.error('Stack {} failed to delete with reason: {}'.format(stack_id, str(e)))
                return False
        else:
            logger.debug('Cluster {} not managed by this provisioner'.format(cluster_id))
            return False
