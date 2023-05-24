"""This implements the 'Manage Documents' feature in the app."""
import os
import shutil
import logging as log
import sqlite3
from llama_index import GPTVectorStoreIndex, SimpleDirectoryReader
from contextlib import closing

from .config import get_upload_file, get_upload_dir, get_index_dir, get_sqlite_file, get_storage_context, get_service_context


def _run_indexing(space):
    docs = SimpleDirectoryReader(get_upload_dir(space)).load_data()
    # Use default storage and service context to initialise index purely for persisting
    index = GPTVectorStoreIndex.from_documents(docs, storage_context=get_storage_context(), service_context=get_service_context())
    index.storage_context.persist(persist_dir=get_index_dir(space))


def upload(file, space):

    with open(get_upload_file(space, file.name), 'wb') as f:
        f.write(file.getvalue())

    _run_indexing(space)


def download(file, space):
    raise NotImplementedError


def delete(filename, space):

    file = get_upload_file(space, filename)
    os.remove(file)

    _run_indexing(space)


def delete_all(space):
    shutil.rmtree(get_upload_dir(space))

    _run_indexing(space)


def show(space):

    return list(map(lambda f: (f.name, f.stat().st_ctime, f.stat().st_size), os.scandir(get_upload_dir(space))))
