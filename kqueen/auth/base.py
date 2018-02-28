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
