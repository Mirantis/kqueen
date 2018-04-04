from .base import BaseAuth

from kqueen.config import current_config
import ldap
import logging

logger = logging.getLogger('kqueen_api')
config = current_config()


class LDAPAuth(BaseAuth):
    def __init__(self, *args, **kwargs):
        """
        Implementation of :func:`~kqueen.auth.base.__init__`
        """

        super(LDAPAuth, self).__init__(*args, **kwargs)

        if not hasattr(self, 'uri'):
            raise Exception('Parameter uri is required')

        self.connection = ldap.initialize(self.uri)

    @staticmethod
    def _email_to_dn(email):
        """This function reads email and converts it to LDAP dn

        Args:
            email (str): e-mail address

        Returns:
            dn (str): LDAP dn, like 'cn=admin,dc=example,dc=org'
        """

        segments = []
        if '@' in email:
            cn, dcs = email.split('@')
        else:
            cn = email
            dcs = ''

        if cn:
            segments.append('cn={}'.format(cn))

        if '.' in dcs:
            for s in dcs.split('.'):
                segments.append('dc={}'.format(s))

        return ','.join(segments)

    def verify(self, user, password):
        """Implementation of :func:`~kqueen.auth.base.__init__`

        This function tries to bind LDAP and returns result.

        Args:
            username (str): Username to login, will be overriden if ldap_config exist.
            password (str): Password, will be overriden if ldap_config exist.

        Returns:
            None: Invalid credentials, Authentication failure.
            User: authenticated user.
        """

        dn = self._email_to_dn(user.username)

        try:
            bind = self.connection.simple_bind_s(dn, password)

            if bind:
                return user, None
        except ldap.INVALID_CREDENTIALS:
            logger.exception("Invalid LDAP credentials for {}".format(dn))

            return None, "Invalid LDAP credentials"

        except ldap.INVALID_DN_SYNTAX:
            logger.exception("Invalid DN syntax in configuration: {}".format(dn))

            return None, "Invalid DN syntax"

        except ldap.LDAPError:
            logger.exception("Failed to bind LDAP server")

            return None, "LDAP auth failed, check log for error"

        finally:
            self.connection.unbind()

        return None, "All LDAP authentication methods failed"
