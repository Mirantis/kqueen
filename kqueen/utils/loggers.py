import os
import yaml
import logging.config
import logging


def setup_logging(path='kqueen/utils/logger_config.yml', default_level=logging.INFO):

    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                logging.config.dictConfig(config)
            except Exception as e:
                print(e)
                print('Failed to load configuration file.\
                      Using default configs. Kqueen generic logging, user logging will not work properly')
                logging.basicConfig(level=default_level)
    else:
        logging.basicConfig(level=default_level)
        print('Failed to load configuration file.\
              Using default configs. Kqueen generic logging, user logging will not work properly')
