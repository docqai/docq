"""Functions to manage indices."""

import logging as log
from typing import List

from llama_index.core.indices import DocumentSummaryIndex, VectorStoreIndex
from llama_index.core.indices.base import BaseIndex
from llama_index.core.indices.loading import load_index_from_storage
from llama_index.core.schema import Document
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

import docq

from .domain import SpaceKey
from .model_selection.main import LlmUsageSettingsCollection, ModelCapability, _get_service_context
from .support.store import _get_default_storage_context, _get_storage_context, get_index_dir

tracer = trace.get_tracer(__name__, docq.__version_str__)


@tracer.start_as_current_span("manage_spaces._create_vector_index")
def _create_vector_index(
    documents: List[Document], model_settings_collection: LlmUsageSettingsCollection
) -> VectorStoreIndex:
    # Use default storage and service context to initialise index purely for persisting
    return VectorStoreIndex.from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
    )


@tracer.start_as_current_span("manage_spaces._create_document_summary_index")
def _create_document_summary_index(
    documents: List[Document], model_settings_collection: LlmUsageSettingsCollection
) -> DocumentSummaryIndex:
    """Create a an index of summaries for each document. This doen't create embedding for each node."""
    return DocumentSummaryIndex(embed_summaries=True).from_documents(
        documents,
        storage_context=_get_default_storage_context(),
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
    )


@tracer.start_as_current_span("manage_spaces._persist_index")
def _persist_index(index: BaseIndex, space: SpaceKey) -> None:
    """Persist an Space datasource index to disk."""
    index.storage_context.persist(persist_dir=get_index_dir(space))


@tracer.start_as_current_span(name="_load_index_from_storage")
def _load_index_from_storage(space: SpaceKey, model_settings_collection: LlmUsageSettingsCollection) -> BaseIndex:
    # set service context explicitly for multi model compatibility
    sc = _get_service_context(model_settings_collection)
    return load_index_from_storage(
        storage_context=_get_storage_context(space), service_context=sc, callback_manager=sc.callback_manager
    )


def load_indices_from_storage(
    spaces: List[SpaceKey], model_settings_collection: LlmUsageSettingsCollection
) -> List[BaseIndex]:
    """Return a list of indices for the given list of spaces."""
    with tracer.start_as_current_span("indices_from_spaces") as span:
        indices = []
        for space in spaces:
            try:
                index_ = _load_index_from_storage(space, model_settings_collection)

                log.debug("run_chat(): %s, %s", index_.index_id, space.summary)
                indices.append(index_)
                span.add_event(
                    name="index_appended",
                    attributes={"index_id": index_.index_id, "index_struct_cls": index_.index_struct_cls.__name__},
                )
            except Exception as e:
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
                log.warning(
                    "Index for space '%s' failed to load, skipping. Maybe the index isn't created yet. Error message: %s",
                    space,
                    e,
                )
                continue
        span.add_event("indices_loaded", {"num_indices_loaded": len(indices), "num_spaces_given": len(spaces)})
        return indices
