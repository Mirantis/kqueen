from .base import BaseAuth

import ldap
import logging

logger = logging.getLogger('kqueen_api')


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
            dn (str): LDAP dn, like 'cn=admin,dc=example,dc=org
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

        This function tries to bind LDAP and returns result
        """

        dn = self._email_to_dn(user.username)

        try:
            bind = self.connection.simple_bind_s(dn, password)

            if bind:
                return user, None
        except ldap.INVALID_CREDENTIALS:
            logger.exception("Invalid LDAP credentials for {}".format(dn))

            return None, "Invalid LDAP credentials"

        except ldap.LDAPError as e:
            logger.exception(e)

            return None, "LDAP auth failed, check log for error"

        finally:
            self.connection.unbind()

        return None, "All LDAP authentication methods failed"
