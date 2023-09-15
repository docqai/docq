"""Initialize Docq."""
import logging

from docq import manage_organisations

from . import manage_settings, manage_space_groups, manage_spaces, manage_user_groups, manage_users


def _config_logging() -> None:
    """Configure logging."""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


def init() -> None:
    """Initialize Docq."""
    _config_logging()
    manage_space_groups._init()
    manage_organisations._init()
    manage_user_groups._init()
    manage_settings._init()
    manage_spaces._init()
    manage_users._init()
    manage_organisations._init_default_org_if_necessary()
    manage_users._init_admin_if_necessary()
    logging.info("Docq initialized")
