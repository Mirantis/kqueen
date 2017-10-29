import os
import importlib

CONFIG_FILE_DEFAULT = 'config/dev.py'


def select_file(config_file=None):
    """
    Select file to be used as a configuration.

    Attributes:
        config_file (str): Filename to be used as a configuration file

    Returns:
        str: filename to be used as a configuration file
    """

    if not config_file:
        config_file = os.environ.get('KQUEEN_CONFIG_FILE')

    if not config_file or config_file == 'None':
        config_file = CONFIG_FILE_DEFAULT

    return config_file


def apply_env_changes(config, prefix='KQUEEN_'):
    """
    Read env variables starting with prefix and apply
    them to existing configuration

    Attributes:
        config (obj): Connfiguration object. This configuration will updated.
        prefix (str): Prefix for environment variables. Defaults to `KQUEEN_`.

    """

    for name, value in os.environ.items():
        if name.startswith(prefix):
            setattr(config, name, value)


def current_config(config_file=None):
    read_file = select_file(config_file)
    module_name = read_file.replace('/', '.').replace('.py', '')

    module = importlib.import_module('kqueen.{}'.format(module_name))
    config = getattr(module, 'Config')

    setattr(config, 'source_file', read_file)

    apply_env_changes(config)

    return config
