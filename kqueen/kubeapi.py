from kubernetes import config, client
from kubernetes.client.rest import ApiException

import logging

# define logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class KubernetesAPI:
    def __init__(self, **kwargs):

        # load configuration
        self.cluster = kwargs['cluster']
        logger.debug('Initialized KubernetesAPI for {}'.format(self.cluster))

        # set apis
        self.api_corev1 = client.CoreV1Api(
            api_client=config.new_client_from_config()
        )

    def list_nodes(self):
        out = []

        try:
            response = self.api_corev1.list_node().items
        except ApiException:
            raise

        for node in response:
            out.append(node.to_dict())

        return out
