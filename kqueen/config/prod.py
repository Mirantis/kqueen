from .base import BaseConfig


class Config(BaseConfig):
    DEBUG = False
    LOG_LEVEL = 'INFO'

    KQUEEN_HOST = '0.0.0.0'
