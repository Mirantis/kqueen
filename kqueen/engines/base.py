from kqueen.config import current_config

import logging

config = current_config()
logger = logging.getLogger(__name__)


class BaseEngine:
    """Base Engine object.

    When you initialize the engine through the prepared property :func:`~kqueen.models.Cluster.engine`
    on :obj:`kqueen.models.Cluster` model object, all keys in engine object parameters attribute (JSONField) on
    :obj:`kqueen.models.Provisioner` object are passed as kwargs.

    Example::
        >>> print my_provisioner.parameters
        {'username': 'foo', 'password': 'bar'}
        >>> print my_cluster.engine.conn_kw
        {'username': 'foo', 'password': 'bar'}

    Credentials passed from parameters attribute to kwargs of MyProvisioner class
    used in conn_kw dict for client initialization.

    Args:
        cluster (:obj:`kqueen.models.Cluster`): Cluster model object related to
        this engine instance.
        **kwargs: Keyword arguments specific to Provisioner implementation.

    Attributes:
        cluster (:obj:`kqueen.models.Cluster`): Cluster model object related to
        this engine instance.
        name (str): Name of the engine usable by program.
        verbose_name (str): Human readable name of the engine.
        parameter_schema (dict): Dictionary representation of the parameters with hints for form rendering.::

            {
                'provisioner': {
                    'username': {
                        'type': 'text',
                        'validators': {
                            'required': True
                        }
                    },
                    'password': {
                        'type': 'password',
                        'validators': {
                            'required': True
                        }
                    }
                }
                'cluster': {
                    'node_count': {
                        'type': 'integer',
                        'validators: {
                            'required': True
                        }
                    }
                }
            }
    """
    name = 'base'
    verbose_name = 'Base Engine'
    parameter_schema = {}

    def __init__(self, cluster, **kwargs):
        self.cluster = cluster

    def cluster_list(self):
        """Get all clusters available on backend.

        Returns:
            list: list of dictionaries. Dictionary format should be::

                {
                    'key': key,     # this record should be cached under this key if you choose to cache
                    'name': name,   # name of the cluster in its respective backend
                    'id': id,       # id of `kqueen.models.Cluster` object in KQueen database
                    'state': state, # cluster.state
                    'metadata': {
                        'foo': bar  # any keys specific for the Provisioner implementation
                    }
                }
        """
        raise NotImplementedError

    def cluster_get(self):
        """Get single cluster from backend related to this engine instance.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object for which we want to get data from backend.

        Returns:
            dict: Dictionary format should be::

                {
                    'key': key,     # (str) this record should be cached under this key if you choose to cache
                    'name': name,   # (str) name of the cluster in its respective backend
                    'id': id,       # (str or UUID) id of `kqueen.models.Cluster` object in KQueen database
                    'state': state, # (str) state of cluster on backend represented by app.config['CLUSTER_[FOO]_STATE']
                    'metadata': {
                        'foo': bar  # any keys specific for the Provisioner implementation
                    }
                }
        """
        raise NotImplementedError

    def provision(self):
        """Provision the cluster related to this engine instance to backend.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to provision to backend.

        Returns:
            tuple: First item is bool (success/failure), second item is error, can be None::

                (True, None)                            # successful provisioning
                (False, 'Could not connect to backend') # failed provisioning
        """
        raise NotImplementedError

    def deprovision(self):
        """Deprovision the cluster related to this engine instance from backend.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to remove from backend.

        Returns:
            tuple: First item is bool (success/failure), second item is error, can be None::

                (True, None)                            # successful provisioning
                (False, 'Could not connect to backend') # failed provisioning
        """
        try:
            cluster = self.cluster_get()
        except NotImplementedError:
            pass
        except Exception as e:
            msg = 'Fetching data from backend for cluster {} failed with following reason: {}'.format(self.cluster_id, repr(e))
            logger.error(msg)
        else:
            if not cluster:
                return True, None

        msg = 'Deprovision method on engine {} is not implemented'.format(self.verbose_name)
        return False, msg

    def resize(self, node_count):
        """Resize the cluster related to this engine instance.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to resize.

        Returns:
            tuple: First item is bool (success/failure), second item is error, can be None::

                (True, None)                            # successful provisioning
                (False, 'Could not connect to backend') # failed provisioning
        """
        raise NotImplementedError

    def get_kubeconfig(self):
        """Get kubeconfig of the cluster related to this engine from backend.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to get kubeconfig for.

        Returns:
            dict: Dictionary form of kubeconfig (`yaml.load(kubeconfig_file)`)
        """
        raise NotImplementedError

    @classmethod
    def get_parameter_schema(cls):
        """Return parameters specific for this Provisioner implementation.

        This method should return parameters specific to the Provisioner implementation,
        these are used to generate form for creation of Provisioner object and are stored
        in parameters attribute (JSONField) of the `kqueen.models.Provisioner` object.

        Returns:
            dict:  Returns ``self.parameter_schema`` in default, but can be overridden.
        """
        return cls.parameter_schema

    def get_progress(self):
        """Get progress of provisioning if its possible to determine.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to get provisioning progress for.

        Returns:
            dict: Dictionary representation of the provisioning provress.::

                {
                    'response': response, # (int) any number other than 200 means failure to determine progress
                    'progress': progress, # (int) provisioning progress in percents
                    'result': result      # (str) current state of the cluster, i.e. 'Deploying'
                }
        """
        raise NotImplementedError

    @staticmethod
    def engine_status():
        """Check if backend this Provisioner implements is reachable and/or working.

        Returns:
            str: Return status of engine, should use statuses from ``app.config``
        """
        return config.get('PROVISIONER_OK_STATE')
