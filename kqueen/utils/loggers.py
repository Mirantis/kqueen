import os
import yaml
import logging.config
import logging


def setup_logging(path, debug_mode):
    default_level = 'INFO'

    if os.path.exists(path):
        with open(path, 'rt') as f:
            try:
                config = yaml.safe_load(f.read())
                loggers = config['loggers']
                for logger, value in loggers.items():
                    if debug_mode:
                        loggers[logger]['level'] = 'DEBUG'
                    else:
                        current_level = value.get('level')
                        loggers[logger]['level'] = default_level if not current_level else current_level

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
