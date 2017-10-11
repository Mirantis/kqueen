from typing import List, Dict, Any


class Provisioner:
    def __init__(self, *args, **kwargs):
        raise NotImplementedError

    def list(self):
        """This is an example of a module level function.
    
        Function parameters should be documented in the ``Args`` section. The name
        of each parameter is required. The type and description of each parameter
        is optional, but should be included if not obvious.
    
        If \*args or \*\*kwargs are accepted,
        they should be listed as ``*args`` and ``**kwargs``.
    
        The format for a parameter is::
    
            name (type): description
                The description may span multiple lines. Following
                lines should be indented. The "(type)" is optional.
    
                Multiple paragraphs are supported in parameter
                descriptions.
    
        Args:
            param1 (int): The first parameter.
            param2 (:obj:`str`, optional): The second parameter. Defaults to None.
                Second line of description should be indented.
            *args: Variable length argument list.
            **kwargs: Arbitrary keyword arguments.
    
        Returns:
            bool: True if successful, False otherwise.
    
            The return type is optional and may be specified at the beginning of
            the ``Returns`` section followed by a colon.
    
            The ``Returns`` section may span multiple lines and paragraphs.
            Following lines should be indented to match the first line.
    
            The ``Returns`` section supports any reStructuredText formatting,
            including literal blocks::
    
                {
                    'param1': param1,
                    'param2': param2
                }
    
        Raises:
            AttributeError: The ``Raises`` section is a list of all exceptions
                that are relevant to the interface.
            ValueError: If `param2` is equal to `param1`.
    
        """
        raise NotImplementedError

    def get(self):
        """
        Get single cluster from backend
        """
        raise NotImplementedError

    def provision(self, cluster_id):
        """
        Provision cluster to backend
        """
        raise NotImplementedError

    def deprovision(self, cluster_id):
        """
        Deprovision cluster from backend
        """
        raise NotImplementedError

    def get_kubeconfig(self, cluster_external_id):
        """
        Return kubeconfig for specified cluster from backend
        """
        raise NotImplementedError

    def get_parameters(self):
        """
        Return parameters this provisioner requires
        """
        raise NotImplementedError

    def get_progress(self):
        """
        Return progress of provisioning
        """
        raise NotImplementedError

    @staticmethod
    def check_backend():
        """
        Check if we can reach the backend this provisioner implements
        """
        raise NotImplementedError

