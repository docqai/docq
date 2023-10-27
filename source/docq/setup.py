"""Initialize Docq."""
import logging

from . import (
    manage_credetials,
    manage_organisations,
    manage_settings,
    manage_space_groups,
    manage_spaces,
    manage_user_groups,
    manage_users,
)
from .support import auth_utils, llm, metadata_extractors, store


def _config_logging() -> None:
    """Configure logging."""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(process)d %(levelname)s %(message)s", force=True) # force over rides Otel (or other) logging config with this.


def init() -> None:
    """Initialize Docq."""
    _config_logging()
    manage_space_groups._init()
    manage_organisations._init()
    manage_user_groups._init()
    manage_credetials._init()
    manage_settings._init()
    manage_spaces._init()
    manage_users._init()
    store._init()
    manage_organisations._init_default_org_if_necessary()
    manage_users._init_admin_if_necessary()
    auth_utils.init_session_cache()
    llm._init_local_models()
    metadata_extractors._cache_metadata_extractor_models()
    logging.info("Docq initialized")
