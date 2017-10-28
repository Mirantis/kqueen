import os
import importlib

CONFIG_FILE_DEFAULT = 'config/dev.py'


def select_file(config_file=None):
    if not config_file:
        config_file = os.environ.get('KQUEEN_CONFIG_FILE')

    if not config_file or config_file == 'None':
        config_file = CONFIG_FILE_DEFAULT

    return config_file


def current_config(config_file=None):
    read_file = select_file(config_file)
    module_name = read_file.replace('/', '.').replace('.py', '')

    module = importlib.import_module('kqueen.{}'.format(module_name))
    config = getattr(module, 'Config')

    setattr(config, 'source_file', read_file)

    return config
