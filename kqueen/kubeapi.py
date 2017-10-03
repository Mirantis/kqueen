from kubernetes import config, client
from kubernetes.client.rest import ApiException

import logging
import yaml

# define logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class KubernetesAPI:
    def __init__(self, **kwargs):
        # load configuration
        try:
            self.cluster = kwargs['cluster']
        except KeyError:
            raise ValueError('Missing parameter cluster')

        logger.debug('Initialized KubernetesAPI for {}'.format(self.cluster))

        self.kubeconfig_file = self.get_kubeconfig_file()
        print(self.kubeconfig_file)

        # set apis
        api_client = config.new_client_from_config(config_file=self.kubeconfig_file)
        self.api_corev1 = client.CoreV1Api(
            api_client=api_client,
        )
        self.api_version = client.VersionApi(
            api_client=api_client,
        )

    def get_kubeconfig_file(self):
        # TODO: make configfile name random
        configfile = '/tmp/kubernetes'

        f = open(configfile, 'w')
        f.write(yaml.dump(self.cluster.kubeconfig.value, indent=2))
        f.close()

        return configfile

    def get_version(self):
        return self.api_version.get_code().to_dict()

    def list_nodes(self):
        out = []

        try:
            response = self.api_corev1.list_node().items
        except ApiException:
            raise

        for node in response:
            out.append(node.to_dict())

        return out

    def list_pods(self):
        """List pods in all namespaces"""
        out = []

        try:
            response = self.api_corev1.list_pod_for_all_namespaces(
                include_uninitialized=True
            ).items
        except ApiException:
            raise

        for pod in response:
            out.append(pod.to_dict())

        return out
