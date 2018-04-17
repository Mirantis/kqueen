class BaseAuth:
    RESERVED_KWARGS = ['verify']

    def __init__(self, *args, **kwargs):
        """Create auth object and establish connection

        Args:
            **kwargs: Keyword arguments specific to Auth engine
        """

        for k, v in kwargs.items():
            if k not in self.RESERVED_KWARGS:
                setattr(self, k, v)

    def verify(self, user, password):
        """Vefifies username and password.

        Args:
            user (User): user object to verify
            password (str): Password to verify

        Returns:
            tuple: (user, error)
                user (User): User object if username and password matched, None otherwise
                error (string): Error message explaing authentication error
        """

        raise NotImplementedError

    @classmethod
    def get_parameter_schema(cls):
        """Return parameters specific for a auth method implementation.

        These parameters are used to generate form for inviting user with fields,
        specific for a particular authentication method.

        Returns:
            dict:  Returns ``self.parameter_schema`` by default, but can be overridden.
        """
        if not hasattr(cls, 'parameter_schema'):
            raise NotImplementedError('"parameter_schema" attribute should be provided in the '
                                      'auth method implementation')
        return cls.parameter_schema
