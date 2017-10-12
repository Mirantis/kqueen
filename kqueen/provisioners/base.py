class Provisioner:
    """Base Provisioner object.

    When you initialize the provisioner through the prepared property :func:`~kqueen.models.Cluster.provisioner_instance`
    on :obj:`kqueen.models.Cluster` model object, all keys in provisioner object parameters attribute (JSONField) on
    :obj:`kqueen.models.Provisioner` object are passed as kwargs.

    Example::
        >>> print my_provisioner.parameters
        {'username': 'foo', 'password': 'bar'}
        >>> print my_cluster.provisioner_instance.conn_kw
        {'username': 'foo', 'password': 'bar'}

    Credentials passed from parameters attribute to kwargs of MyProvisioner class
    used in conn_kw dict for client initialization.

    Args:
        cluster (:obj:`kqueen.models.Cluster`): Cluster model object related to
            this provisioner instance.
        **kwargs: Keyword arguments specific to Provisioner implementation.

    Attributes:
        cluster (:obj:`kqueen.models.Cluster`): Cluster model object related to
            this provisioner instance.
    """

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
        """Get single cluster from backend related to this provisioner instance.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object for which we want to get data from backend.

        Returns:
            dict: Dictionary format should be::

                {
                    'key': key,     # (str) this record should be cached under this key if you choose to cache
                    'name': name,   # (str) name of the cluster in its respective backend
                    'id': id,       # (str or UUID) id of `kqueen.models.Cluster` object in KQueen database
                    'state': state, # (str) cluster.state
                    'metadata': {
                        'foo': bar  # any keys specific for the Provisioner implementation
                    }
                }
        """
        raise NotImplementedError

    def provision(self):
        """Provision the cluster related to this provisioner instance to backend.

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
        """Deprovision the cluster related to this provisioner instance from backend.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to remove from backend.

        Returns:
            tuple: First item is bool (success/failure), second item is error, can be None::

                (True, None)                            # successful provisioning
                (False, 'Could not connect to backend') # failed provisioning
        """
        raise NotImplementedError

    def get_kubeconfig(self):
        """Get kubeconfig of the cluster related to this provisioner from backend.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to get kubeconfig for.

        Returns:
            dict: Dictionary form of kubeconfig (`yaml.load(kubeconfig_file)`)
        """
        raise NotImplementedError

    def get_parameter_schema(self):
        """Return parameters specific for this Provisioner implementation.

        This method should return parameters specific to the Provisioner implementation,
        these are used to generate form for creation of Provisioner object and are stored
        in parameters attribute (JSONField) of the `kqueen.models.Provisioner` object.

        Returns:
            dict: Dictionary representation of the parameters with hints for form rendering.::

                {
                    'username': {
                        'type': 'text',
                        'required': True,
                        'initial': None
                    }
                    'password': {
                        'type': 'password',
                        'required': True,
                        'initial': None
                    }
                }
        """
        raise NotImplementedError

    def get_progress(self):
        """Get progress of provisioning if its possible to determine.

        Although this function doesn't take any arguments, it is expected that
        the implementation of the Provisioner gets ``self.cluster`` to provide the
        relevant object which we want to get provisioning progress for.

        Returns:
            dict: Dictionary representation of the provisioning provress.::

                {
                    'response': response, # (int) any number other than 0 means failure to determine progress
                    'progress': progress, # (int) provisioning progress in percents
                    'result': result      # (str) current state of the cluster, i.e. 'Deploying'
                }
        """
        raise NotImplementedError

    @staticmethod
    def provisioner_status():
        """Check if backend this Provisioner implements is reachable and/or working.

        Returns:
            str: Return status of provisioner, should use statuses from ``app.config``
        """
        raise NotImplementedError

