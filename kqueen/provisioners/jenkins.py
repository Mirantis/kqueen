from pprint import pprint
from werkzeug.contrib.cache import SimpleCache

import jenkins
import json
import logging
import requests
import yaml

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

cache = SimpleCache()


class JenkinsProvisioner():
    def __init__(self, *args, **kwargs):
        # configuration
        self.jenkins_url = kwargs.get('jenkins_url', 'https://ci.mcp.mirantis.net')
        self.job_name = kwargs.get('job_name', 'deploy-aws-k8s_ha_calico')

        self.server = jenkins.Jenkins(self.jenkins_url)

        self.provisioner = 'jenkins'
        self.cache_timeout = 5 * 60

    def get_job(self):
        return self.server.get_job_info(self.job_name)

    def list(self):
        job = self.get_job()

        clusters = {}

        for build in job['builds']:
            logger.debug('Reading build {}'.format(build))

            cluster_id = 'cluster-{}-{}'.format(self.provisioner, build['number'])
            clusters[cluster_id] = cache.get(cluster_id)

            if clusters[cluster_id] is None:
                logger.debug('Build {} missing in cache'.format(cluster_id))
                build_info = self.server.get_build_info(self.job_name, build['number'])

                if build_info['result'] in ['SUCCESS'] and build_info.get('description'):
                    stack_name = build_info['description'].split(' ')[0]

                    clusters[cluster_id] = {
                        'name': stack_name,
                        'artifacts': [],
                        'state': 'DEPLOYED',
                    }

                    ## parse artifacts
                    #if build_info.get('artifacts'):
                    #    for a in build_info['artifacts']:
                    #        clusters[cluster_id]['artifacts'].append(a['relativePath'])

                   ## read outputs and kubeconfig
                    #for f in ['outputs.json', 'kubeconfig']:
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
                else:
                    clusters[cluster_id] = {'state': 'FAILED'}

                cache.set(cluster_id, clusters[cluster_id], timeout=self.cache_timeout)

        return clusters
