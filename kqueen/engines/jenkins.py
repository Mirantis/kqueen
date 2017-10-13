from flask import current_app as app
from kqueen.engines.base import BaseEngine
from kqueen.server import cache

import jenkins
import logging
import requests
import time
import yaml

# Ugly patch to make this module importable outside app context to generate docs
if not app:
    import kqueen.config.dev as config_dev
    app = type(
        'app',
        (object,),
        {'config': {k: v for (k, v) in config_dev.__dict__.items() if not k.startswith("__")}}
    )

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


STATE_MAP = {
    'ABORTED': app.config['CLUSTER_ERROR_STATE'],
    'FAILURE': app.config['CLUSTER_ERROR_STATE'],
    'NOT_BUILT': app.config['CLUSTER_UNKNOWN_STATE'],
    'SUCCESS': app.config['CLUSTER_OK_STATE'],
    'UNSTABLE': app.config['CLUSTER_UNKNOWN_STATE']
}


class JenkinsEngine(BaseEngine):
    name = 'jenkins'
    verbose_name = 'Jenkins'
    jenkins_url = app.config['JENKINS_API_URL']
    username = app.config['JENKINS_USERNAME']
    password = app.config['JENKINS_PASSWORD']
    provision_job_name = app.config['JENKINS_PROVISION_JOB_NAME']
    anchor_parameter = app.config['JENKINS_ANCHOR_PARAMETER']
    parameter_schema = {
        'username': {
            'type': 'text',
            'required': True,
            'initial': None
        },
        'password': {
            'type': 'password',
            'required': True,
            'initial': None
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

    def _get_provision_job_builds(self):
        """
        Get builds history of Jenkins job used to provision clusters

        Returns:
            dict: More information at :func:`~jenkins.Jenkins.get_job_info`
        """
        return self.client.get_job_info(self.provision_job_name, depth=1)

    @classmethod
    def engine_status(cls):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.engine_status`
        """
        conn_kw = {
            'username': app.config['JENKINS_USERNAME'],
            'password': app.config['JENKINS_PASSWORD']
        }
        status = app.config['PROVISIONER_UNKNOWN_STATE']
        try:
            client = jenkins.Jenkins(app.config['JENKINS_API_URL'], **conn_kw)
            version = client.get_version()
            if version:
                status = app.config['PROVISIONER_OK_STATE']
        except Exception as e:
            logger.error('Could not contact JenkinsEngine backend: {}'.format(repr(e)))
            status = app.config['PROVISIONER_ERROR_STATE']
        return status

    def _get_client(self):
        """
        Initialize Jenkins client

        Returns:
            :obj:`jenkins.Jenkins`: initialized Jenkins client
        """
        return jenkins.Jenkins(self.jenkins_url, **{
            'username': self.username,
            'password': self.password
        })

    def provision(self, **kwargs):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.provision`
        """
        cluster_id = self.cluster.id
        ctx = app.config['JENKINS_PROVISION_JOB_CTX']
        # PATCH THE CTX TO CONTAIN ANCHOR WITH OBJ UUID
        ctx['STACK_NAME'] = 'KQUEEN__{}'.format(cluster_id)
        try:
            self.client.build_job(self.provision_job_name, ctx)
            return (True, None)
        except Exception as e:
            msg = 'Creating cluster {} failed with following reason: {}'.format(cluster_id, repr(e))
            logger.error(msg)
            return (False, msg)
        return (None, None)

    def get_kubeconfig(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_kubeconfig`
        """
        cluster_external_id = self._get_external_id()
        if not cluster_external_id:
            return {}
        kubeconfig_url = '{jenkins_url}/job/{job_name}/{build_id}/artifact/kubeconfig'.format(
            jenkins_url=self.jenkins_url,
            job_name=self.provision_job_name,
            build_id=str(cluster_external_id),
        )
        kubeconfig = {}
        try:
            kubeconfig = yaml.load(requests.get(kubeconfig_url).text)
        except Exception as e:
            logger.error(repr(e))
        return kubeconfig

    def _get_external_id(self):
        """
        Get external ID of cluster, in this case Jenkins job ID.

        First we try to get external_id from related object metadata, if there is no external_id
        yet, we need to look it up in build history of our configured provisioning Jenkins job

        Returns:
            int: Jenkins job ID
        """
        metadata = self.cluster.metadata or {}
        external_id = metadata.get('external_id', None)
        if external_id:
            return external_id
        try:
            cluster = self._get_by_id()
            external_id = cluster['metadata']['external_id']
            # Get fresh data just in case to avoid conflict
            metadata = self.cluster.metadata or {}
            metadata['external_id'] = external_id
            self.cluster.metadata = metadata
            self.cluster.save()
            return external_id
        except:
            pass
        return external_id

    def _get_by_id(self):
        cluster_id = self.cluster.id
        _list = self.cluster_list()
        cluster = [c for c in _list if c['id'] == cluster_id]
        return cluster[0] if cluster else {}

    def _get_by_external_id(self):
        cluster_external_id = self._get_external_id()
        # Cannot get by external_id if there is no external_id on self.cluster
        if not cluster_external_id:
            return {}
        # Try to get the data from cache
        cluster_cache_key = 'cluster-{}-{}'.format(self.name, cluster_external_id)
        cluster = cache.get(cluster_cache_key)
        if cluster:
            return cluster
        # Get build info for the given job ID (external_id)
        build = self.client.get_build_info(self.provision_job_name, int(cluster_external_id))
        cluster = self._get_cluster_from_build(build)
        return cluster or {}

    def cluster_get(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.cluster_get`

        First we try to get cluster by external_id, because its much more efficient in this
        implementation. If its not possible yet, we return from the slower method
        """
        cluster = self._get_by_external_id()
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
            _cluster_id = [p.get('value', '') for p in parameters
                           if p.get('name', '') == 'STACK_NAME' and p.get('value', '').startswith('KQUEEN')]
            cluster_id = _cluster_id[0].split('__')[1] if _cluster_id else None

            # Try to determine cluster state
            if build['result']:
                try:
                    state = STATE_MAP[build['result']]
                except KeyError:
                    logger.warning('{} is not valid cluster state'.format(build['result']))
                    state = app.config['CLUSTER_UNKNOWN_STATE']
            else:
                state = app.config['CLUSTER_PROVISIONING_STATE']

            cluster = {
                'key': cluster_cache_key,
                'name': stack_name,
                'id': cluster_id,
                'state': state,
                'metadata': {
                    'external_id': build['number'],
                    'build_timestamp': build['timestamp'],
                    'build_estimated_duration': build['estimatedDuration']
                }
            }

            if cluster['state'] != app.config['CLUSTER_PROVISIONING_STATE']:
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
        response = 0
        progress = 1
        result = app.config['CLUSTER_UNKNOWN_STATE']
        try:
            cluster = self.cluster_get()
            result = cluster['state']
            if cluster['state'] == app.config['CLUSTER_PROVISIONING_STATE']:
                # Determine approximate percentage of progress, it is based on estimation
                # from Jenkins, so it can get above 99 percent without being done, so there
                # is patch to hold it on 99 untill its actually done
                now = time.time() * 1000
                start = cluster['metadata']['build_timestamp']
                estimate = cluster['metadata']['build_estimated_duration']
                progress = int(((now - start) / estimate) * 100)
                if progress > 99:
                    progress = 99
            else:
                progress = 100
        except:
            response = 1
        return {'response': response, 'progress': progress, 'result': result}

    def get_parameter_schema(self):
        """
        Implementation of :func:`~kqueen.engines.base.BaseEngine.get_parameter_schema`
        """
        return self.parameter_schema
