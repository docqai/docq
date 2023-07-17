import logging

from .manage_users import _init_admin_if_necessary


def _config_logging():
    logging.basicConfig(level=logging.DEBUG)


def init():
    _config_logging()
    _init_admin_if_necessary()
    logging.info("Docq initialized")
