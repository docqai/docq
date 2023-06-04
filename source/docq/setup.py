import os
import logging
import streamlit as st

def _load_env_vars():

    for k in ['DOCQ_DATA', 'OPENAI_API_KEY']:
        if k not in os.environ:
            if k in st.secrets:
                logging.debug(f'{k} not found as environment variable. Loading from secrets.toml.')
                os.environ[k] = st.secrets[k]
            else:
                logging.error(f'{k} not set as environment variable or in secrets.toml. dfg')

def _config_logging():
    logging.basicConfig(level=logging.DEBUG)

def _setup_persistance_folder():
    try:
        if not os.path.exists(os.environ["DOCQ_DATA"]):
            os.makedirs(os.environ["DOCQ_DATA"])
            logging.info(f'Created folder `{os.environ["DOCQ_DATA"]}` because it didn\'t exist.')
    except OSError as e:
        logging.error(f'Error creating folder `{os.environ["DOCQ_DATA"]}`: {e}')

def init():
    _config_logging()
    _load_env_vars()
    _setup_persistance_folder()
    logging.info("Docq initialized with env vars: %s", os.environ)
