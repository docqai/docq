"""Integration tests."""

from dotenv import load_dotenv

load_dotenv("pytest.env")
print("Loaded pytest.env")

import logging

logging.disable(logging.CRITICAL)
