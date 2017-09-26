from werkzeug.contrib.cache import SimpleCache
from base import Provisioner

import jenkins
import logging
import requests
import yaml

from flask import current_app as app

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cache = SimpleCache()


class JenkinsProvisioner(Provisioner):
    def __init__(self, *args, **kwargs):
        # configuration
        self.jenkins_url = kwargs.get('jenkins_url', app.config['JENKINS_API_URL'])
        conn_kw = {
            'username': kwargs.get('username', app.config['JENKINS_USERNAME']),
            'password': kwargs.get('password', app.config['JENKINS_PASSWORD'])
        }
        self.client = jenkins.Jenkins(self.jenkins_url, **conn_kw)

        self.provisioner = 'jenkins'
        self.cache_timeout = 5 * 60
        self.job_name = kwargs.get('job_name', app.config['JENKINS_JOB_NAME'])

    def get_job(self):
        return self.client.get_job_info(self.job_name, depth=1)

    def provision(self, obj_id, **kwargs):
        # TODO: write extension for Python Jenkins so we can catch headers and return
        # queue item ID in jenkins.build_job response which we can immediatelly save
        # on Cluster object and keep working with it, so we can avoid using anchor to
        # distinguish which builds were triggered by this app
        # More informations here: https://issues.jenkins-ci.org/browse/JENKINS-12827
        ctx = kwargs.get('job_ctx', app.config['JENKINS_JOB_CTX'])
        # PATCH THE CTX TO CONTAIN ANCHOR WITH OBJ UUID
        ctx['STACK_NAME'] = 'KQUEEN__%s' % str(obj_id)
        try:
            self.client.build_job(self.job_name, ctx)
            return True
        except Exception as e:
            logging.error('Creating cluster %s failed with following reason: %s' % (obj_id, repr(e)))
        return False

    def get_kubeconfig(self, job_number):
        kubeconfig_url = '%s/job/%s/%s/artifact/kubeconfig' % (
            self.jenkins_url, self.job_name, str(job_number))
        kubeconfig = {}
        try:
            kubeconfig = yaml.load(requests.get(kubeconfig_url).text)
        except Exception as e:
            logger.error(repr(e))
        return kubeconfig

    def get(self, obj_id):
        _list = self.list()
        for key, value in _list.items():
            if obj_id == value['obj_id']:
                return value
        return {}

    def list_clusters(self):
        job = self.get_job()
        clusters = {}

        for build in job['builds']:
            logger.debug('Reading build {}'.format(build))

            cluster_id = 'cluster-{}-{}'.format(self.provisioner, build['number'])
            clusters[cluster_id] = cache.get(cluster_id)

            if clusters[cluster_id] is None:
                logger.debug('Build {} missing in cache'.format(cluster_id))
                _parameters = [d for d in build.get('actions', []) if d.get('parameters', [])]
                parameters = _parameters[0].get('parameters', []) if _parameters else []

                stack_name = ''
                if build['result'] in ['SUCCESS'] and build.get('description'):
                    stack_name = build['description'].split(' ')[0]
                # LOOKUP STACKS WITH OUR ANCHOR AND DON'T THINK ABOUT IT TOO MUCH
                _obj_id = [p.get('value', '') for p in parameters if p.get('name', '') == 'STACK_NAME' and p.get('value', '').startswith('KQUEEN')]
                obj_id = _obj_id[0].split('__')[1] if _obj_id else None

                clusters[cluster_id] = {
                    'name': stack_name,
                    'artifacts': [],
                    'obj_id': obj_id,
                    'build_number': build['number'],
                    'build_timestamp': build['timestamp'],
                    'build_estimated_duration': build['estimatedDuration'],
                    'state': build['result'] if build['result'] else 'Deploying'
                }

                # parse artifacts
                # if build_info.get('artifacts'):
                #    for a in build_info['artifacts']:
                #        clusters[cluster_id]['artifacts'].append(a['relativePath'])

                # read outputs and kubeconfig
                # for f in ['outputs.json', 'kubeconfig']:
                #    url = '{}/{}/{}'.format(
                #        build_info['url'],
                #        'artifact',
                #        f
                #    )
                #    logger.debug('Downloading ' + url)
                #    response = requests.get(url)
                #    if response.status_code == 200:
                #        if f.endswith('.json'):
                #            content = response.json()
                #        elif f.endswith('.yml') or f == 'kubeconfig':
                #            content = yaml.load(response.text)
                #        else:
                #            content = response.text

                #        clusters[cluster_id]['config'][f] = content
                if clusters[cluster_id]['state'] != 'Deploying':
                    cache.set(cluster_id, clusters[cluster_id], timeout=self.cache_timeout)
                # ONLY GET 5 LATEST BUILDS

        return clusters
