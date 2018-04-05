from kqueen.config import current_config


class AuthModules():
    """
    Authentication Modules

    To define new module, need to specify it as dictionary, where:

    auth_option_lower_case = {"engine": "EqualsToAuthClassName",
                               "param": {
                                   "key": "value"
                               }
                               }
    """

    config = current_config()
    ldap = {"engine": "LDAPAuth",
            "param": {
                "uri": config.get('LDAP_URI')
            }
            }
    local = {"engine": "LocalAuth",
             "param": {}
             }
