from kqueen.engines.base import BaseEngine
from kqueen.server import cache
from kqueen.config import current_config

import jenkins
import logging
import requests
import time
import yaml

logger = logging.getLogger('kqueen_api')
config = current_config()


STATE_MAP = {
    'ABORTED': config.get('CLUSTER_ERROR_STATE'),
    'FAILURE': config.get('CLUSTER_ERROR_STATE'),
    'NOT_BUILT': config.get('CLUSTER_UNKNOWN_STATE'),
    'SUCCESS': config.get('CLUSTER_OK_STATE'),
    'UNSTABLE': config.get('CLUSTER_UNKNOWN_STATE')
}


class JenkinsEngine(BaseEngine):
    name = 'jenkins'
    verbose_name = 'Jenkins'
    jenkins_url = config.get('JENKINS_API_URL')
    username = config.get('JENKINS_USERNAME')
    password = config.get('JENKINS_PASSWORD')
    provision_job_name = config.get('JENKINS_PROVISION_JOB_NAME')
    deprovision_job_name = config.get('JENKINS_DEPROVISION_JOB_NAME')
    job_parameter_map = config.get('JENKINS_PARAMETER_MAP')
    parameter_schema = {
        'provisioner': {
            'username': {
                'type': 'text',
                'label': 'Username',
                'order': 0,
                'validators': {
                    'required': True
                }
            },
            'password': {
                'type': 'password',
                'label': 'Password',
                'order': 1,
                'validators': {
                    'required': True
                }
            }
            'override_parameters': {
                'type': 'text',
                'label': 'Key=Value line by line',
                'order': 2,
            },
        },
        'cluster': {
            'network_policy': {
                'type': 'select',
                'choices': [
                    ('calico', 'Calico Network Provider'),
                ],
                'label': 'Network Policy',
                'order': 3,
             },
            'enable_policy': {
                'type': 'checkbox',
                'label': 'Network Policy',
                'order': 4,
                'checkbox_text': 'Enable Network Policy (2 or more nodes are required)',
                'class_name': 'nwpolicy-checkbox'
             }
            'network_range': {
                'type': 'string',
                'label': 'Network Range',
                'default': 5,
                'validators': {
                #TODO CIDR validation
                }
            }
        }
    }

    def __init__(self, cluster, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.__init__`
        """
        # Call parent init to save cluster on self
        super(JenkinsEngine, self).__init__(cluster, **kwargs)
        # Client initialization
        self.username = kwargs.get('username', self.username)
        self.password = kwargs.get('password', self.password)
        self.client = self._get_client()
        # Cache settings
        self.cache_timeout = 5 * 60
        self.cluster_config = {
            'cluster': {
                'name': self.cluster_id,
                'networkPolicy': {
                    'provider': kwargs.get('network_policy', 'calico')
                    'enabled': kwargs.get('enable_policy', False)
                    'network_range': kwargs.get('network_range', {})
                }
            }
        }
        self.job_override_params = kwargs.get('override_parameters', [])

    def _get_provision_job_builds(self):
        """
        Get builds history of Jenkins job used to provision clusters

        Returns:
            dict: More information at :func:`~jenkins.Jenkins.get_job_info`
        """
        return self.client.get_job_info(self.provision_job_name, depth=1)

    def _parse(self):
        """
        Get builds history of Jenkins job used to provision clusters

        Returns:
            dict: More information at :func:`~jenkins.Jenkins.get_job_info`
        """
        return self.client.get_job_info(self.provision_job_name, depth=1)

    @classmethod
    def engine_status(cls, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.engine_status`
        """
        conn_kw = {
            'username': kwargs.get('username', config.get('JENKINS_USERNAME')),
            'password': kwargs.get('password', config.get('JENKINS_PASSWORD')),
            'timeout': 10
        }
        status = config.get('PROVISIONER_UNKNOWN_STATE')
        try:
            client = jenkins.Jenkins(config.get('JENKINS_API_URL'), **conn_kw)
            auth_verify = client.get_whoami()
            if auth_verify:
                status = config.get('PROVISIONER_OK_STATE')
        except Exception as e:
            logger.exception('Could not contact JenkinsEngine backend: ')
            status = config.get('PROVISIONER_ERROR_STATE')
        return status

    def _get_client(self):
        """
        Initialize Jenkins client

        Returns:
            :obj:`jenkins.Jenkins`: initialized Jenkins client
        """
        return jenkins.Jenkins(self.jenkins_url, **{
            'username': self.username,
            'password': self.password,
            'timeout': 10
        })

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        ctx = config.get('JENKINS_PROVISION_JOB_CTX')
        cluster_name = self.job_parameter_map['cluster_name']
        cluster_uuid = self.job_parameter_map['cluster_uuid']
        # PATCH THE CTX TO CONTAIN CLUSTER NAME AND UUID
        ctx[cluster_name] = 'kqueen-{}'.format(self.cluster.id)
        ctx[cluster_uuid] = self.cluster.id
        try:
            self.client.build_job(self.provision_job_name, ctx)
            return True, None
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason: '.format(self.cluster.id)
            logger.exception(msg)
            return False, msg
        return None, None

    def deprovision(self, **kwargs):
        """
        Deprovisioning isn't supported for Jenkins provisioner yet.

        Implementation of :func:`~kqueen.engines.base.BaseEngine.deprovision`
        """
        ctx = config.get('JENKINS_DEPROVISION_JOB_CTX')
        cluster_name = self.job_parameter_map['cluster_name']
        ctx[cluster_name] = 'kqueen-{}'.format(self.cluster.id)
        try:
            self.client.build_job(self.deprovision_job_name, ctx)
            return True, None
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason:'.format(self.cluster.id)
            logger.exception(msg)
            return False, msg
        return None, None

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        cluster_build_number = self._get_build_number()
        if not cluster_build_number:
            return {}
        kubeconfig_url = '{job_url}/artifact/kubeconfig'.format(job_url=self._get_jenkins_job_url(cluster_build_number))
        kubeconfig = {}
        try:
            kubeconfig = yaml.load(requests.get(kubeconfig_url).text)
        except Exception as e:
            logger.exception('Error')
        return kubeconfig

    def _get_build_number(self):
        """
        Get external ID of cluster, in this case Jenkins job ID.

        First we try to get build_number from related object metadata, if there is no build_number
        yet, we need to look it up in build history of our configured provisioning Jenkins job

        Returns:
            int: Jenkins job ID
        """
        metadata = self.cluster.metadata or {}
        build_number = metadata.get('build_number', None)
        if build_number:
            return build_number
        try:
            cluster = self._get_by_id()
            build_number = cluster['metadata']['build_number']
            self._save_cluster_metadata(build_number)
            return build_number
        except Exception:
            pass
        return build_number

    def _save_cluster_metadata(self, build_number):
        # Get fresh data just in case to avoid conflict
        metadata = self.cluster.metadata or {}
        metadata['build_number'] = build_number
        metadata['job_url'] = self._get_jenkins_job_url(build_number)
        self.cluster.metadata = metadata
        self.cluster.save()

    def _get_by_id(self):
        cluster_id = self.cluster.id
        _list = self.cluster_list()
        cluster = [c for c in _list if c['id'] == cluster_id]
        return cluster[0] if cluster else {}

    def _get_by_build_number(self):
        cluster_build_number = self._get_build_number()
        # Cannot get by build_number if there is no build_number on self.cluster
        if not cluster_build_number:
            return {}
        # Try to get the data from cache
        cluster_cache_key = 'cluster-{}-{}'.format(self.name, cluster_build_number)
        cluster = cache.get(cluster_cache_key)
        if cluster:
            return cluster
        # Get build info for the given job ID (build_number)
        build = self.client.get_build_info(self.provision_job_name, int(cluster_build_number))
        cluster = self._get_cluster_from_build(build)
        return cluster or {}

    def _get_jenkins_job_url(self, build_number):
        return '{jenkins_url}/job/{job_name}/{build_number}'.format(jenkins_url=self.jenkins_url,
                                                                    job_name=self.provision_job_name,
                                                                    build_number=build_number)

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        First we try to get cluster by build_number, because its much more efficient in this
        implementation. If its not possible yet, we return from the slower method
        """
        cluster = self._get_by_build_number()
        if cluster:
            return cluster
        return self._get_by_id()

    def _get_cluster_from_build(self, build):
        cluster_cache_key = 'cluster-{}-{}'.format(self.name, build['number'])
        cluster = cache.get(cluster_cache_key)

        if cluster is None:
            logger.debug('Build {} missing in cache'.format(cluster_cache_key))

            # Prepare build parameters
            _parameters = [d for d in build.get('actions', []) if d.get('parameters', [])]
            parameters = _parameters[0].get('parameters', []) if _parameters else []

            # Try to determine stack name on backend
            stack_name = ''
            if build['result'] in ['SUCCESS'] and build.get('description'):
                stack_name = build['description'].split(' ')[0]

            # Try to determine cluster_id
            cluster_uuid_parameter = self.job_parameter_map['cluster_uuid']
            _cluster_id = [p.get('value', '') for p in parameters
                           if p.get('name', '') == cluster_uuid_parameter]
            cluster_id = _cluster_id[0] if _cluster_id else None

            # Try to determine cluster state
            if build['result']:
                try:
                    state = STATE_MAP[build['result']]
                except KeyError:
                    logger.exception('{} is not valid cluster state'.format(build['result']))
                    state = config.get('CLUSTER_UNKNOWN_STATE')
            else:
                state = config.get('CLUSTER_PROVISIONING_STATE')

            cluster = {
                'key': cluster_cache_key,
                'name': stack_name,
                'id': cluster_id,
                'state': state,
                'metadata': {
                    'build_number': build['number'],
                    'build_timestamp': build['timestamp'],
                    'build_estimated_duration': build['estimatedDuration']
                }
            }

            if cluster['state'] != config.get('CLUSTER_PROVISIONING_STATE'):
                cache.set(cluster_cache_key, cluster, timeout=self.cache_timeout)

        return cluster

    def cluster_list(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_list`
        """
        job = self._get_provision_job_builds()
        clusters = []

        for build in job['builds']:
            logger.debug('Reading build {}'.format(build))
            cluster = self._get_cluster_from_build(build)
            clusters.append(cluster)

        return clusters

    def get_progress(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_progress`
        """
        response = 200
        progress = 1
        result = config.get('CLUSTER_UNKNOWN_STATE')
        try:
            cluster = self.cluster_get()
            result = cluster['state']
            if cluster['state'] == config.get('CLUSTER_PROVISIONING_STATE'):
                # Determine approximate percentage of progress, it is based on estimation
                # from Jenkins, so it can get above 99 percent without being done, so there
                # is patch to hold it on 99 untill its actually done
                now = time.time() * 1000
                start = cluster['metadata']['build_timestamp']
                estimate = cluster['metadata']['build_estimated_duration']
                progress = int(((now - start) / estimate) * 100)
                if estimate == -1:
                    raise ArithmeticError
                if progress > 99:
                    progress = 99
            else:
                progress = 100
        except ArithmeticError:
            raise NotImplementedError
        except Exception:
            response = 500
        return {'response': response, 'progress': progress, 'result': result}
