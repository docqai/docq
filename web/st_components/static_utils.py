"""Utility functions for static files."""
from typing import Optional


def load_file_variables(file_path: str, vars_: Optional[dict] = None) -> str:
    """Load file variables."""
    with open(file_path) as f:
        file_str = f.read()
        if vars_:
            for key, value in vars_.items():
                if value is not None:
                    file_str = file_str.replace('{{' + key + '}}', value)
        return file_str
