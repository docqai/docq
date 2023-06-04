import os
import logging
import streamlit as st

def _load_env_vars():

    for k in ['DOCQ_DATA', 'OPENAI_API_KEY']:
        if k not in os.environ:
            if k in st.secrets:
                os.environ[k] = st.secrets[k]
            else:
                logging.error(f'{k} not set as environment variable or in secrets.toml.')

def _config_logging():
    logging.basicConfig(level=logging.DEBUG)


def init():
    _load_env_vars()
    _config_logging()
    logging.info("Docq initialized with env vars: %s", os.environ)
