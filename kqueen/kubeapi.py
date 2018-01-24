"""Kubernetes client wrapper."""


from kubernetes import client
from kubernetes.config.kube_config import KubeConfigLoader
from kubernetes.client.rest import ApiException
from kqueen.helpers import prefix_to_num

import logging

# define logging
logger = logging.getLogger(__name__)


class KubernetesAPI:
    """Kubernetes API client."""

    def __init__(self, **kwargs):
        """
        Set cluster and prepare clients for all used resource types.

        Args:
            **kwargs: Keyword arguments (cluster is required)
        """
        # load configuration
        try:
            self.cluster = kwargs['cluster']
        except KeyError:
            raise ValueError('Missing parameter cluster')

        logger.debug('Initialized KubernetesAPI for {}'.format(self.cluster))

        # set apis
        api_client = self.get_api_client()

        self.api_corev1 = client.CoreV1Api(api_client=api_client)
        self.api_extensionsv1beta1 = client.ExtensionsV1beta1Api(api_client=api_client)
        self.api_rbacauthorizationv1beta1 = client.RbacAuthorizationV1beta1Api(api_client=api_client)
        self.api_version = client.VersionApi(api_client=api_client)

    def get_api_client(self):
        """
        Create Kubernetes API client with configuration from string.

        Returns:
            str: Kubeconfig file path

        """

        # This super-ugly code configuration is causes by wrong design of config-loading
        # functions in https://github.com/kubernetes-client/python
        client_config = type.__call__(client.Configuration)
        kubeconfig = self.cluster.get_kubeconfig()
        kcl = KubeConfigLoader(
            config_dict=kubeconfig,
        )
        kcl.load_and_set(client_config)

        return client.ApiClient(configuration=client_config)

    def get_version(self):
        """Return Kubernetes version."""
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

    def list_persistent_volumes(self):
        out = []

        try:
            response = self.api_corev1.list_persistent_volume().items
        except ApiException:
            raise

        for pv in response:
            out.append(pv.to_dict())

        return out

    def list_service_accounts(self):
        out = []

        try:
            response = self.api_corev1.list_service_account_for_all_namespaces().items
        except ApiException:
            raise

        for service_account in response:
            out.append(service_account.to_dict())

        return out

    def list_cluster_roles(self):
        out = []

        try:
            response = self.api_rbacauthorizationv1beta1.list_cluster_role().items
        except ApiException:
            raise

        for cluster_role in response:
            out.append(cluster_role.to_dict())

        return out

    def list_cluster_role_bindings(self):
        out = []

        try:
            response = self.api_rbacauthorizationv1beta1.list_cluster_role_binding().items
        except ApiException:
            raise

        for cluster_rb in response:
            out.append(cluster_rb.to_dict())

        return out

    def list_persistent_volume_claims(self):
        out = []

        try:
            response = self.api_corev1.list_persistent_volume_claim_for_all_namespaces().items
        except ApiException:
            raise

        for pvc in response:
            out.append(pvc.to_dict())

        return out

    def list_namespaces(self):
        out = []

        try:
            response = self.api_corev1.list_namespace().items
        except ApiException:
            raise

        for namespace in response:
            out.append(namespace.to_dict())

        return out

    def list_pods(self, include_uninitialized=True):
        """List pods in all namespaces."""
        out = []

        try:
            response = self.api_corev1.list_pod_for_all_namespaces(
                include_uninitialized=include_uninitialized
            ).items
        except ApiException:
            raise

        for pod in response:
            out.append(pod.to_dict())

        return out

    def list_pods_by_node(self):
        out = {
            'Unknown': []
        }
        try:
            nodes = self.list_nodes()
            pods = self.list_pods()
        except ApiException:
            raise

        for node in nodes:
            out[node['metadata']['name']] = []

        for pod in pods:
            node = pod['spec'].get('node_name', 'Unknown') or 'Unknown'
            out[node].append(pod)

        return out

    def count_pods_by_node(self):
        out = {}

        try:
            pods = self.list_pods_by_node()
        except ApiException:
            raise

        for node_name, pods in pods.items():
            out[node_name] = len(pods)

        return out

    def resources_by_node(self):
        """Read pods on each node, compute sum or requested and limited resources.

        Returns:
            Dict of nodes with allocated resources.
            CPU is float.
            Memory int is in bytes.

        .. code:: yaml

            {
                'node1': {
                    'limits': {'cpu': 2, 'mem': 100},
                    'requests': {'cpu': 1.5, 'mem': 10098}
                }
            }

        """
        out = {}

        try:
            pods = self.list_pods_by_node()
        except ApiException:
            raise

        for node_name, pods in pods.items():
            if node_name not in out:
                out[node_name] = {'limits': {'cpu': 0, 'memory': 0}, 'requests': {'cpu': 0, 'memory': 0}}

            for pod in pods:
                containers = pod.get('spec', {}).get('containers', [])
                for c in containers:
                    resources = c.get('resources')

                    if resources:
                        for resource_policy in ['limits', 'requests']:
                            policy = resources.get(resource_policy, {})

                            if policy:
                                for resource_type in ['cpu', 'memory']:
                                    value = policy.get(resource_type)

                                    if value:
                                        out[node_name][resource_policy][resource_type] += prefix_to_num(value)

        return out

    def _extract_annotation(self, service, prefix='kqueen/'):
        """Read service and return kqueen annotations (if present).

        Args:
            service (dict)
            prefix (str): default `kqueen/`

        Return:
            dict: Annotations matching prefix
        """
        out = {}

        annotations = service.get('metadata', {}).get('annotations', {})

        if annotations:
            for an_name, an in annotations.items():
                if an_name.startswith(prefix):
                    out[an_name[len(prefix):]] = an

        return out

    def list_services(self, include_uninitialized=True, filter_addons=False):
        """List services in all namespaces."""
        out = []

        try:
            response = self.api_corev1.list_service_for_all_namespaces(
                include_uninitialized=include_uninitialized
            ).items
        except ApiException:
            raise

        for item in response:
            if filter_addons:
                addon = self._extract_annotation(item.to_dict())
                if addon:
                    out.append(addon)
            else:
                out.append(item.to_dict())

        return out

    def list_deployments(self, include_uninitialized=True):
        """List deployments in all namespaces."""
        out = []

        try:
            response = self.api_extensionsv1beta1.list_deployment_for_all_namespaces(
                include_uninitialized=include_uninitialized
            ).items
        except ApiException:
            raise

        for item in response:
            out.append(item.to_dict())

        return out

    def list_replica_sets(self, include_uninitialized=True):
        """List replica sets in all namespaces."""
        out = []

        try:
            response = self.api_extensionsv1beta1.list_replica_set_for_all_namespaces(
                include_uninitialized=include_uninitialized
            ).items
        except ApiException:
            raise

        for item in response:
            out.append(item.to_dict())

        return out
