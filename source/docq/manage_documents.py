"""Functions to manage documents."""

import os
import shutil

from .domain import SpaceKey
from .support.llm import reindex
from .support.store import get_upload_dir, get_upload_file


def upload(filename: str, content: bytes, space: SpaceKey) -> None:
    """Upload the file to the space."""
    with open(get_upload_file(space, filename), "wb") as f:
        f.write(content)

    reindex(space)


def get_file(filename: str, space: SpaceKey) -> str:
    """Return the path to the file in the space."""
    raise get_upload_file(space, filename)


def delete(filename: str, space: SpaceKey) -> None:
    """Delete the file from the space."""
    file = get_upload_file(space, filename)
    os.remove(file)

    reindex(space)


def delete_all(space: SpaceKey) -> None:
    """Delete all files in the space."""
    shutil.rmtree(get_upload_dir(space))

    reindex(space)


def list_all(space: SpaceKey) -> list[tuple[str, int, int]]:
    """Return a list of tuples containing the filename, creation time, and size of each file in the space."""
    return list(map(lambda f: (f.name, f.stat().st_ctime, f.stat().st_size), os.scandir(get_upload_dir(space))))
