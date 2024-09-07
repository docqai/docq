"""Integration tests."""
import os

from dotenv import load_dotenv

dotenv_file = "pytest.env"
if not os.path.isfile(dotenv_file):
    raise FileNotFoundError(f"Tests: File '{dotenv_file}' not found.")

load_dotenv(dotenv_file)
print("Loaded pytest.env")

import logging

logging.disable(logging.CRITICAL)
