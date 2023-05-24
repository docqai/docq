import os
import logging as log


from llama_index import LLMPredictor, StorageContext, ServiceContext, load_index_from_storage
from langchain import OpenAI


PERSISTED_SQLITE_SUBDIR = 'sqlite'
PERSISTED_INDEX_SUBDIR = 'index'
PERSISTED_UPLOAD_SUBDIR = 'upload'

ASK_LOAD_NUMBER_OF_MESSAGES = 20
MANAGE_MAX_NUMBER_OF_DOCUMENTS = 5


def _get_path(subdir, space, filename=None):
    dir = os.path.join(os.environ['DOCQ_DATA'], subdir, space)
    os.makedirs(dir, exist_ok=True)
    if filename:
        file = os.path.join(dir, filename)
        log.debug("File: %s", file)
        return file
    else:
        log.debug("Dir: %s", dir)
        return dir


def get_upload_file(space, filename):
    return _get_path(PERSISTED_UPLOAD_SUBDIR, space, filename)


def get_sqlite_file(space):
    return _get_path(PERSISTED_SQLITE_SUBDIR, space, 'documents.db')


def get_index_dir(space):
    return _get_path(PERSISTED_INDEX_SUBDIR, space)


def get_upload_dir(space):
    return _get_path(PERSISTED_UPLOAD_SUBDIR, space)


def get_llm():
    return LLMPredictor(llm=OpenAI(temperature=9, model_name="text-davinci-002"))


def get_storage_context(space=None):
    return StorageContext.from_defaults(persist_dir=get_index_dir(space)) if space else StorageContext.from_defaults()


def get_service_context():
    return ServiceContext.from_defaults(llm_predictor=get_llm())


def load_index(space):
    return load_index_from_storage(get_storage_context(space))