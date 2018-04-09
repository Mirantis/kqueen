from .base import BaseAuth

from kqueen.config import current_config
from kqueen.exceptions import ImproperlyConfigured
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
        if not all(hasattr(self, attr) for attr in ['uri', 'admin_dn', 'password']):
            logger.error('Failed to configure LDAP synchronization error.')
            raise ImproperlyConfigured

        # Define Kqueen rdn for all dc's
        dc_list = []
        for i in ldap.dn.explode_dn(self.admin_dn):
            if i.startswith('dc='):
                dc_list.append(i)
        self.kqueen_dc = ','.join(dc_list)

        # Bind connection for Kqueen Read-only user
        if self._bind(self.admin_dn, self.password):
            self.connection = ldap.initialize(self.uri)
            self.connection.simple_bind_s(self.admin_dn, self.password)
            self.connection.protocol_version = ldap.VERSION3
        else:
            logger.error('Failed to bind connection for Kqueen Read-only user')
            self.connection.unbind()

    def _get_matched_dn(self, cn):
        """This function reads username as cn and returns all matched full-dn's

        Args:
            cn (str): Username of invited user

        Returns:
            matched_dn (list): List of all matched dn's in groups.
        """

        base_dn = self.kqueen_dc
        search_scope = ldap.SCOPE_SUBTREE
        retrieveAttributes = ['dn']
        search_filter = "(cn={})".format(cn)
        search_result = self.connection.search_s(base_dn, search_scope, search_filter, retrieveAttributes)

        if search_result:
            matched_dn = [dn[0] for dn in search_result]
            logger.debug('Matched to RegExp DN key: {}'.format(matched_dn))
        else:
            logger.error('No matches to user {},{} found:'.format(matched_dn))

        self.connection.unbind()
        return matched_dn

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

        if user.metadata.get('ldap_dn', None):
            logger.debug('Full dn already stored in user metadata: {}'.format(user.metadata))
            if self._bind(user.metadata['ldap_dn'], password):
                logger.debug('LDAP Verification through metadata: {} passed successfully'.format(user.metadata))
                return user, None
        else:
            logger.debug('There is no dn in user metadata: {}, searching in LDAP...'.format(user.metadata))
            matched_dn = self._get_matched_dn(user.username)
            full_dn = None

            for dn in matched_dn:
                if self._bind(dn, password):
                    full_dn = dn

            if full_dn:
                user.metadata['ldap_dn'] = full_dn
                user.save()
                logger.debug('Valid full-DN found: {}. It will be stored in user metadata: {}'.format(full_dn, user.metadata))
                logger.debug('LDAP Verification passed successfully')
                return user, None

        return None, "Verification failed"

    def _bind(self, dn, password):

        try:
            self.connection = ldap.initialize(self.uri)
            bind = self.connection.simple_bind_s(dn, password)

            if bind:
                return True
        except ldap.INVALID_CREDENTIALS:
            logger.exception("Invalid LDAP credentials for {}".format(dn))

            return False

        except ldap.INVALID_DN_SYNTAX:
            logger.exception("Invalid DN syntax in configuration: {}".format(dn))

            return False

        except ldap.LDAPError:
            logger.exception("Failed to bind LDAP server")

            return False

        except Exception:
            logger.exception("Unknown error occurred during LDAP server bind")

            return False

        finally:
            self.connection.unbind()

        return False, "All LDAP authentication methods failed"
