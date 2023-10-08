"""Initialize Docq."""
import logging
import os

import llama_index

from . import (
    manage_organisations,
    manage_settings,
    manage_space_groups,
    manage_spaces,
    manage_user_groups,
    manage_users,
)
from .support import auth_utils, llm, store


def _config_logging() -> None:
    """Configure logging."""
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s %(message)s")


def _config_observability() -> None:
    """Configure observability."""
    # _config_arize_phoenix()
    # _config_wandb()


def _config_arize_phoenix() -> None:
    """Configure arize_phoenix."""
    import phoenix as px

    # Look for a URL in the output to open the App in a browser.
    logging.info("Launching Phoenix App...")
    px.launch_app()

    # The App is initially empty, but as you proceed with the steps below,
    # traces will appear automatically as your LlamaIndex application runs.

    llama_index.set_global_handler("arize_phoenix")


def _config_wandb() -> None:
    """Configure wandb."""
    import wandb

    WANDB_PROJECT_NAME = os.environ["DOCQ_WANDB_PROJECT"]
    WANDB_API_KEY = os.environ["DOCQ_WANDB_API_KEY"]
    wandb.login(key=WANDB_API_KEY)
    llama_index.set_global_handler("wandb", run_args={"project": WANDB_PROJECT_NAME})


def init() -> None:
    """Initialize Docq."""
    _config_logging()
    _config_observability()
    manage_space_groups._init()
    manage_organisations._init()
    manage_user_groups._init()
    manage_settings._init()
    manage_spaces._init()
    manage_users._init()
    store._init()
    manage_organisations._init_default_org_if_necessary()
    manage_users._init_admin_if_necessary()
    auth_utils.init_session_cache()
    llm._init_local_models()
    logging.info("Docq initialized")
