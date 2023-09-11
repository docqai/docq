import logging

from . import manage_settings, manage_space_groups, manage_spaces, manage_user_groups, manage_users
from .support import auth_utils, store


def _config_logging():
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


def init():
    _config_logging()
    manage_space_groups._init()
    manage_user_groups._init()
    manage_settings._init()
    manage_spaces._init()
    manage_users._init()
    manage_users._init_admin_if_necessary()
    auth_utils.init_session_cache()
    store._init()
    logging.info("Docq initialized")
