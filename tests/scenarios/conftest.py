"""A module for configuring pytest to include new features.

This module provides a function to add new features automatically
as test files in pytest. The new features will trigger errors because
steps are not implemented.
"""
from pathlib import Path

import pytest
from pytest_bdd.feature import get_features
from pytest_bdd.scenario import get_features_base_dir
from pytest_bdd.utils import get_caller_module_path


def pytest_configure(config: pytest.Config) -> None:
    """Configure tests to include new features.

    This function adds new features automatically as test files.
    Adding new features will trigger errors because steps are not implemented.

    Args:
        config (Config): Configuration provided by pytest.

    """
    conftest_dir = Path(__file__).parent
    caller_module_path = Path(get_caller_module_path())
    features_base_dir = Path(get_features_base_dir(caller_module_path))
    if features_base_dir.exists():
        features = get_features([features_base_dir])
    else:
        features = []

    for feat in features:

        feature_dir = Path(feat.filename).parent
        file_dir = (
            conftest_dir / "steps" / feature_dir.relative_to(features_base_dir)
        )
        file_name = Path(feat.filename).stem + "_test.py"
        file_path = file_dir / file_name
        feature_rel_path = Path(feat.filename).relative_to(features_base_dir)
        txt = (
            '"""Feature steps implementation.\n'
            "\n"
            f'Source file: {feature_rel_path}\n"""\n'
            "from pytest_bdd import scenarios\n"
            "\n"
            f"""scenarios("{feature_rel_path}")"""
        )

        file_dir.mkdir(parents=True, exist_ok=True)

        if not file_path.exists():
            with open(file_path, "w") as f:
                f.write(txt)
