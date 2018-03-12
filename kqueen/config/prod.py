from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_LEVEL = 'DEBUG'
    LOG_CONFIG = 'kqueen/utils/logger_config.yml'

    KQUEEN_HOST = '0.0.0.0'
