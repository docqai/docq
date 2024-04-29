"""Initialize Docq."""
import logging
import os

from opentelemetry import trace

import docq
from docq import db_migrations, extensions, manage_assistants

from . import (
    integrations,
    manage_organisations,
    manage_settings,
    manage_space_groups,
    manage_spaces,
    manage_user_groups,
    manage_users,
    services,
)
from .config import ENV_VAR_DOCQ_LOGLEVEL
from .support import auth_utils, llm, store

tracer = trace.get_tracer(__name__, docq.__version_str__)

def _config_logging() -> None:
    """Configure logging."""
    log_level = os.environ.get(ENV_VAR_DOCQ_LOGLEVEL, "ERROR")

    logging.basicConfig(
        level=log_level.upper(), format="%(asctime)s %(process)d %(levelname)s %(message)s", force=True
    )  # force overrides Otel (or other) logging config with this.


#FIXME: right now this will run everytime a user hits the home page. add a global lock using st.cache to make this only run once.
def init() -> None:
    """Initialize Docq."""
    with tracer.start_as_current_span("docq.setup.init") as span:
        _config_logging()
        extensions._extensions_init()
        manage_space_groups._init()
        manage_organisations._init()
        manage_user_groups._init()
        manage_settings._init()
        manage_spaces._init()
        manage_users._init()
        manage_assistants._init()
        db_migrations.run() # run db migrations after all tables are created
        services._init()
        integrations._init()
        services.credential_utils.setup_all_service_credentials()
        store._init()
        manage_organisations._init_default_org_if_necessary()
        manage_users._init_admin_if_necessary()
        auth_utils.init_session_cache()
        llm._init_local_models()
        #metadata_extractors._cache_metadata_extractor_models()
        logging.info("Docq initialized")
        span.add_event("Docq initialized")

        logging.error("Docq error test message")