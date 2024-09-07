"""Docq module."""
import importlib.metadata as __metadata__

if __package__ is not None:
    _pkg_metadata = __metadata__.metadata(__package__).json
    project_urls = {}
    for item in _pkg_metadata["project_url"]:
        key, value = item.split(", ")
        project_urls[key] = value

    # data from pyproject.toml
    __version__ = _pkg_metadata["version"]  # version field
    __version_str__ = str(__version__)
    __summary__ = _pkg_metadata["summary"]  # description field
    __description__ = _pkg_metadata["description"]  # readme field
    __homepage_url__ = _pkg_metadata["home_page"]  # homepage field
    __documentation_url__ = project_urls["Documentation"]  # documentation field
    __repository_url__ = project_urls["Repository"]  # repository field
    __author_email__ = _pkg_metadata["author_email"]  # authors field
    __maintainer_email__ = _pkg_metadata["maintainer_email"]  # maintainers field
else:
    raise ValueError("Package name is not defined")

__all__ = [
    "config",
    "manage_users",
    "manage_documents",
    "manage_spaces",
    "manage_sharing",
    "setup",
    "run_queries",
]
