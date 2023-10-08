"""Page: Dev"""

import asyncio
import logging
import os
from typing import Any, Callable, Dict, List, Optional, Sequence, cast

import numpy as np
import pandas as pd
import phoenix as px
import streamlit as st
import streamlit.components.v1 as components
from docq.config import ENV_VAR_DOCQ_DATA, SpaceType
from docq.data_source.list import SpaceDataSources
from docq.domain import SpaceKey
from docq.manage_spaces import get_space_data_source
from docq.model_selection.main import ModelUsageSettingsCollection, get_saved_model_settings_collection
from docq.support.llm import (
    _get_completion_model,
    _get_embed_model,
    _get_llm_predictor,
    _get_storage_context,
)
from docq.support.store import _StoreSubdir
from llama_index import (
    ComposableGraph,
    Document,
    DocumentSummaryIndex,
    KnowledgeGraphIndex,
    ServiceContext,
    StorageContext,
    SummaryIndex,
    TreeIndex,
    VectorStoreIndex,
    get_response_synthesizer,
    load_graph_from_storage,
    load_index_from_storage,
)
from llama_index.callbacks import CallbackManager, OpenInferenceCallbackHandler
from llama_index.callbacks.base import BaseCallbackHandler
from llama_index.callbacks.open_inference_callback import as_dataframe
from llama_index.evaluation import RetrieverEvaluator
from llama_index.indices.base import BaseIndex
from llama_index.node_parser import SimpleNodeParser
from llama_index.node_parser.extractors import (
    EntityExtractor,
    KeywordExtractor,
    MetadataExtractor,
)
from llama_index.node_parser.extractors.metadata_extractors import MetadataFeatureExtractor
from llama_index.query_engine import BaseQueryEngine, RetrieverQueryEngine
from llama_index.response_synthesizers.type import ResponseMode
from llama_index.retrievers import VectorIndexRetriever
from llama_index.schema import BaseNode
from phoenix import EmbeddingColumnNames, TraceDataset
from phoenix.experimental.evals.retrievals import (
    classify_relevance,
    compute_precisions_at_k,
)
from phoenix.trace.llama_index import (
    OpenInferenceTraceCallbackHandler,
)
from phoenix.trace.span_json_encoder import spans_to_jsonl
from phoenix.trace.utils import json_lines_to_df
from pydantic import Field, PrivateAttr
from st_pages import add_page_title
from utils.handlers import list_shared_spaces
from utils.layout import auth_required
from utils.sessions import get_selected_org_id

auth_required(requiring_admin=True)

add_page_title()

# to create a new experiment, add a new key here and a new value to.
# key= exp_id aka experiment id
# value = exp friendly name
experiments = {
    "graph_index_1": "Graph Index 1",
    "kg_index_1": "KG Index 1",
}


def _get_exp_path(
    store: _StoreSubdir, type_: SpaceType, subtype: str = None, filename: str = None, makedir: bool = True
) -> str:
    logging.debug("_get_path() - store: %s, type_: %s, subtype: %s, filename: %s", store, type_, subtype, filename)
    dir_ = (
        os.path.join(os.environ[ENV_VAR_DOCQ_DATA], "exp", store.value, type_.name, subtype)
        if subtype
        else os.path.join(os.environ[ENV_VAR_DOCQ_DATA], "exp", store.value, type_.name)
    )
    os.makedirs(dir_, exist_ok=True)
    if filename:
        file_ = os.path.join(dir_, filename)
        logging.debug("File: %s", file_)
        return file_
    else:
        logging.debug("Dir: %s", dir_)
        return dir_


def get_exp_index_dir(space: SpaceKey, exp_id: str, makedir: bool = True) -> str:
    """Get the index directory for a space."""
    return (
        _get_exp_path(store=_StoreSubdir.INDEX, type_=space.type_, subtype=str(space.id_))
        if space.type_ == SpaceType.PERSONAL
        else _get_exp_path(
            store=_StoreSubdir.INDEX,
            type_=space.type_,
            subtype=os.path.join(str(space.org_id), str(space.id_), exp_id),
        )
    )


def _get_exp_trace_dir(space: SpaceKey, exp_id: str, filename: str = None, makedir: bool = True) -> str:
    return (
        _get_exp_path(store=_StoreSubdir.INDEX, type_=space.type_, subtype=str(space.id_))
        if space.type_ == SpaceType.PERSONAL
        else _get_exp_path(
            store=_StoreSubdir.INDEX,
            type_=space.type_,
            subtype=os.path.join(str(space.org_id), str(space.id_), exp_id, "traces"),
            filename=filename,
        )
    )


def _get_exp_storage_context(space: SpaceKey, exp_id: str) -> StorageContext:
    return StorageContext.from_defaults(persist_dir=get_exp_index_dir(space, exp_id))


def _get_exp_service_context(model_settings_collection: ModelUsageSettingsCollection) -> ServiceContext:
    """Get experiments service context."""
    phoenix_trace_callback_handler = OpenInferenceTraceCallbackHandler()
    phoenix_inference_callback_handler = OpenInferenceCallbackHandler()
    cbm = CallbackManager(handlers=[phoenix_trace_callback_handler, phoenix_inference_callback_handler])
    return ServiceContext.from_defaults(
        llm_predictor=_get_llm_predictor(model_settings_collection),
        node_parser=_get_node_parser(model_settings_collection, cbm),
        embed_model=_get_embed_model(model_settings_collection),
        callback_manager=cbm,
    )


def _get_node_parser(
    model_settings_collection: ModelUsageSettingsCollection, callback_manager: CallbackManager
) -> SimpleNodeParser:
    # TitleExtractor(nodes=5),
    # QuestionsAnsweredExtractor(questions=3),
    # SummaryExtractor(summaries=["prev", "self"]),
    # KeywordExtractor(keywords=10, llm_predictor=_get_llm_predictor(model_settings_collection)),

    metadata_extractor = MetadataExtractor(
        extractors=[
            DocqEntityExtractor(label_entities=True, device="cpu", prediction_threshold=0.1),
        ],
    )

    node_parser = (
        SimpleNodeParser.from_defaults(  # SimpleNodeParser is the default when calling ServiceContext.from_defaults()
            metadata_extractor=metadata_extractor,  # adds extracted metadata as metadata
            callback_manager=callback_manager,
        )
    )

    return node_parser


DEFAULT_ENTITY_MAP = {
    "PER": "persons",
    "ORG": "organizations",
    "LOC": "locations",
    "ANIM": "animals",
    "BIO": "biological",
    "CEL": "celestial",
    "DIS": "diseases",
    "EVE": "events",
    "FOOD": "foods",
    "INST": "instruments",
    "MEDIA": "media",
    "PLANT": "plants",
    "MYTH": "mythological",
    "TIME": "times",
    "VEHI": "vehicles",
}

DEFAULT_ENTITY_MODEL = "tomaarsen/span-marker-mbert-base-multinerd"


class DocqEntityExtractor(MetadataFeatureExtractor):
    """Entity extractor. Extracts `entities` into a metadata field using a default model `tomaarsen/span-marker-mbert-base-multinerd` and the SpanMarker library.

    Install SpanMarker with `pip install span-marker`.
    """

    model_name: str = Field(
        default=DEFAULT_ENTITY_MODEL,
        description="The model name of the SpanMarker model to use.",
    )
    prediction_threshold: float = Field(default=0.5, description="The confidence threshold for accepting predictions.")
    span_joiner: str = Field(description="The seperator beween entity names.")
    label_entities: bool = Field(default=False, description="Include entity class labels or not.")
    device: Optional[str] = Field(default=None, description="Device to run model on, i.e. 'cuda', 'cpu'")
    entity_map: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of entity class names to usable names.",
    )

    _tokenizer: Callable = PrivateAttr()
    _model: Any = PrivateAttr()

    def __init__(
        self,
        model_name: str = DEFAULT_ENTITY_MODEL,
        prediction_threshold: float = 0.5,
        span_joiner: str = " ",
        label_entities: bool = False,
        device: Optional[str] = None,
        entity_map: Optional[Dict[str, str]] = None,
        tokenizer: Optional[Callable[[str], List[str]]] = None,
        **kwargs: Any,
    ) -> None:
        """Entity extractor for extracting entities from text and inserting into node metadata.

        Args:
            model_name (str):
                Name of the SpanMarker model to use.
            prediction_threshold (float):
                Minimum prediction threshold for entities. Defaults to 0.5.
            span_joiner (str):
                String to join spans with. Defaults to " ".
            label_entities (bool):
                Whether to label entities with their type. Setting to true can be
                slightly error prone, but can be useful for downstream tasks.
                Defaults to False.
            device (Optional[str]):
                Device to use for SpanMarker model, i.e. "cpu" or "cuda".
                Loads onto "cpu" by default.
            entity_map (Optional[Dict[str, str]]):
                Mapping from entity class name to label.
            tokenizer (Optional[Callable[[str], List[str]]]):
                Tokenizer to use for splitting text into words.
                Defaults to NLTK word_tokenize.
            **kwargs (Any): sdf
        """
        logging.debug("Init DocqEntityExtractor")
        try:
            from span_marker import SpanMarkerModel
        except ImportError as err:
            raise ImportError("SpanMarker is not installed. Install with `pip install span-marker`.") from err

        try:
            from nltk.tokenize import word_tokenize
        except ImportError:
            raise ImportError("NLTK is not installed. Install with `pip install nltk`.")

        self._model = SpanMarkerModel.from_pretrained(model_name)
        if device is not None:
            self._model = self._model.to(device)

        self._tokenizer = tokenizer or word_tokenize

        base_entity_map = DEFAULT_ENTITY_MAP
        if entity_map is not None:
            base_entity_map.update(entity_map)

        super().__init__(
            model_name=model_name,
            prediction_threshold=prediction_threshold,
            span_joiner=span_joiner,
            label_entities=label_entities,
            device=device,
            entity_map=base_entity_map,
            **kwargs,
        )

    @classmethod
    def class_name(cls) -> str:
        """Get class name."""
        return "EntityExtractor"

    def extract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        """Extract node-level entity metadata."""
        metadata_list: List[Dict] = [{} for _ in nodes]
        node_count = len(nodes)
        for i, metadata in enumerate(metadata_list):
            node_text = nodes[i].get_content(metadata_mode=self.metadata_mode)
            # words = self._tokenizer(node_text)
            # spans = self._model.predict(words)
            logging.debug("EntityExtractor: processed node %s of %s: %s", i, node_count, nodes[i].hash)
            logging.debug("EntityExtractor: node text: %s", node_text)
            spans = self._model.predict(node_text)
            logging.debug("EntityExtractor: spans: %s", spans)
            for span in spans:
                if span["score"] > self.prediction_threshold:
                    ent_label = self.entity_map.get(span["label"], span["label"])
                    metadata_label = ent_label if self.label_entities else "entities"

                    if metadata_label not in metadata:
                        metadata[metadata_label] = set()

                    metadata[metadata_label].add(self.span_joiner.join(span["span"]))

        # convert metadata from set to list
        for metadata in metadata_list:
            for key, val in metadata.items():
                metadata[key] = list(val)
        logging.debug("Entities: %s", metadata_list)
        return metadata_list


DEFAULT_EXTRACT_TEMPLATE_STR = """\
Here is the content of the section:
----------------
{context_str}
----------------
Given the contextual information, extract out a {class_name} object.\
"""


def save_phoenix_traces(space: SpaceKey, exp_id: str, callback_handlers: List[BaseCallbackHandler]) -> None:
    """Save phoenix traces.

    Args:
        space (SpaceKey): Space
        exp_id (str): Experiment ID
        callback_handlers (List[BaseCallbackHandler]): List of callback handlers from the service context callback manager
    """
    for h in callback_handlers:
        if isinstance(h, OpenInferenceTraceCallbackHandler):
            path = _get_exp_trace_dir(space, exp_id, "phoenix_trace.jsonl")
            with open(file=path, mode="a", encoding="utf-8") as f:
                f.write(spans_to_jsonl(h.get_spans()))


def load_phoenix_traces(space: SpaceKey, exp_id: str) -> TraceDataset | None:
    """Load phoenix traces."""
    path = _get_exp_trace_dir(space, exp_id, "phoenix_trace.jsonl", makedir=False)
    if not os.path.exists(path):
        return None

    json_lines = []
    with open(file=path, mode="r", encoding="utf-8") as f:
        json_lines = cast(List[str], f.readlines())

    return TraceDataset(json_lines_to_df(json_lines)) if len(json_lines) > 0 else None


def flush_query_buffer_into_phoenix(
    phoenix_session: px.Session, callback_handlers: List[BaseCallbackHandler]
) -> px.Dataset:
    """Flush query buffer into phoenix."""
    for h in callback_handlers:
        if isinstance(h, OpenInferenceCallbackHandler):
            query_data_buffer = h.flush_query_data_buffer()
            query_dataframe = as_dataframe(query_data_buffer)
            # Construct a phoenix dataset directly from the dataframe, no schema needed
            dataset = px.Dataset.from_open_inference(query_dataframe)
            logging.debug("Inference data flushed")
            # phoenix_session.primary_dataset = dataset
    return dataset


def storage_context_to_dataframe(storage_context: StorageContext) -> pd.DataFrame:
    """Converts the storage context to a pandas dataframe.

    Args:
        storage_context (StorageContext): Storage context containing the index
        data.

    Returns:
        pd.DataFrame: The dataframe containing the index data.
    """
    document_ids = []
    document_texts = []
    document_embeddings = []
    docstore = storage_context.docstore
    vector_store = storage_context.vector_store
    for node_id, node in docstore.docs.items():
        document_ids.append(node.hash)  # use node hash as the document ID
        document_texts.append(node.text)
        document_embeddings.append(np.array(vector_store.get(node_id)))
    return pd.DataFrame(
        {
            "document_id": document_ids,
            "text": document_texts,
            "text_vector": document_embeddings,
        }
    )


def load_index(
    space: SpaceKey, model_settings_collection: ModelUsageSettingsCollection, exp_id: str = None
) -> VectorStoreIndex:
    """Load index from storage."""
    storage_context = _get_storage_context(space) if exp_id is None else _get_exp_storage_context(space, exp_id)
    return load_index_from_storage(
        storage_context=storage_context, service_context=_get_exp_service_context(model_settings_collection)
    )


def custom_query_engine(vector_store_index: VectorStoreIndex) -> BaseQueryEngine:
    """Custom query engine."""
    # index = VectorStoreIndex.from_documents(documents)

    # configure retriever
    retriever = VectorIndexRetriever(
        index=vector_store_index,
        similarity_top_k=5,
    )

    # configure response synthesizer
    response_synthesizer = get_response_synthesizer(
        response_mode=ResponseMode.TREE_SUMMARIZE,
        service_context=vector_store_index.service_context,
        callback_manager=vector_store_index.service_context.callback_manager,
    )

    # assemble query engine
    query_engine = RetrieverQueryEngine(
        retriever=retriever,
        response_synthesizer=response_synthesizer,
        callback_manager=vector_store_index.service_context.callback_manager,
    )
    return query_engine


def get_space_document_objects(space: SpaceKey) -> List[Document]:
    """Get space document objects."""
    (ds_type, ds_configs) = get_space_data_source(space)
    documents = []
    try:
        documents = SpaceDataSources[ds_type].value.load(space, ds_configs)

    except Exception as e:
        logging.exception("Error indexing space %s: %s", space, e)

    return documents


def build_summary_index(docs: Sequence[Document], model_settings: ModelUsageSettingsCollection) -> VectorStoreIndex:
    """Build summary index."""
    service_context = _get_exp_service_context(model_settings)
    # https://gpt-index.readthedocs.io/en/stable/core_modules/query_modules/query_engine/response_modes.html
    response_synthesizer = get_response_synthesizer(
        response_mode=ResponseMode.COMPACT, use_async=True, service_context=service_context
    )

    doc_summary_index = DocumentSummaryIndex.from_documents(
        docs,
        service_context=service_context,
        response_synthesizer=response_synthesizer,
    )
    return doc_summary_index


def build_per_doc_tree_index(
    space: SpaceKey, docs: Sequence[Document], model_settings: ModelUsageSettingsCollection, exp_id: str
) -> List[tuple[str, TreeIndex, str]]:
    """Build per doc tree index with summary.

    Returns:
        List of tuples (doc_id, tree_index, summary)
    """
    service_context = _get_exp_service_context(model_settings)

    doc_indexes = []
    for document in docs:
        # storage_context = _get_exp_storage_context(space, os.path.join(exp_id, document.doc_id))
        # build tree index per document (eg PDF or KB article or blog post)
        tree_index = TreeIndex.from_documents([document], service_context=service_context)
        # generate a summary for this document
        # ref; retriever modes https://gpt-index.readthedocs.io/en/latest/core_modules/query_modules/retriever/retriever_modes.html
        summary = tree_index.as_query_engine(retriever_mode="all_leaf").query("What is a summary of this document?")
        doc_indexes.append((document.doc_id, tree_index, str(summary)))
        tree_index.storage_context.persist(persist_dir=get_exp_index_dir(space, os.path.join(exp_id, document.doc_id)))

    return doc_indexes


def build_composable_graph_from_tree_indices(
    space: SpaceKey, tree_indices: List[tuple[str, TreeIndex, str]], exp_id: str
) -> VectorStoreIndex:
    """Build composable graph from tree indices."""
    storage_context = _get_exp_storage_context(space, exp_id)
    # build composable graph
    composable_graph = ComposableGraph.from_indices(
        SummaryIndex,
        [x[1] for x in tree_indices],
        index_summaries=[x[2] for x in tree_indices],
        storage_context=storage_context,
    )

    # set the ID
    composable_graph.root_index.set_index_id(exp_id)

    composable_graph.root_index.storage_context.persist(persist_dir=get_exp_index_dir(space, exp_id))
    return composable_graph


def load_composable_graph_from_tree_indices(space: SpaceKey, exp_id: str) -> ComposableGraph:
    """Build composable graph from tree indices."""
    storage_context = _get_exp_storage_context(space, exp_id)
    return load_graph_from_storage(storage_context, root_id=exp_id)


def build_knowledge_graph(
    space: SpaceKey, docs: Sequence[Document], model_settings: ModelUsageSettingsCollection, exp_id: str
) -> KnowledgeGraphIndex:
    """Build knowledge graph index."""
    # storage_context = _get_exp_storage_context(space, exp_id)
    service_context = _get_exp_service_context(model_settings)

    kg_index = load_knowledge_graph_from_storage(space, exp_id)
    if kg_index:
        logging.debug("Refreshing KG {exp_id}}")
        kg_index.refresh_ref_docs(docs)
    else:
        logging.debug("(re)building KG {exp_id}}")
        kg_index = KnowledgeGraphIndex(include_embeddings=True, service_context=service_context).from_documents(
            docs,
            service_context=service_context,
            max_triplets_per_chunk=5,
        )

    kg_index.storage_context.persist(persist_dir=get_exp_index_dir(space, exp_id))
    return kg_index


def load_knowledge_graph_from_storage(space: SpaceKey, exp_id: str) -> KnowledgeGraphIndex:
    """Load knowledge graph index from storage."""
    storage_context = _get_exp_storage_context(space, exp_id)
    service_context = _get_exp_service_context(saved_model_settings)
    return load_index_from_storage(
        storage_context=storage_context,
        service_context=service_context,
    )


def t(index: BaseIndex) -> (px.Dataset, px.Dataset):
    """Run evaluation."""
    database_df = storage_context_to_dataframe(index.storage_context)
    database_df = database_df.drop_duplicates(subset=["text"])

    "Corpus/Datasource as dataframe:"
    st.write(database_df.dtypes)
    st.write(database_df.head())

    database_df["text_vector"]
    database_df["text_vector"].dtype
    database_centroid = database_df["text_vector"].mean()
    database_df["text_vector"] = database_df["text_vector"].apply(lambda x: x - database_centroid)

    st.write(database_centroid)

    for h in index.service_context.callback_manager.handlers:
        if isinstance(h, OpenInferenceCallbackHandler):
            query_data_buffer = h.flush_query_data_buffer()
    query_df = as_dataframe(query_data_buffer)

    # st.write(query_data_buffer)

    "query as dataframe:"
    st.write(query_df.head())

    st.write(":feature.[float].embedding:prompt")
    st.write(query_df[":feature.[float].embedding:prompt"].dtype)

    # as_dataframe() returns the list of embedding floats with an incorrect type. should be np.ndarray but returns list. so we have to manually convert for now.
    query_centroid = np.array(query_df[":feature.[float].embedding:prompt"]).mean()
    query_df[":feature.[float].embedding:prompt"] = query_df[":feature.[float].embedding:prompt"].apply(
        lambda x: st.write(x, query_centroid)  # np.array(x) - query_centroid
    )

    evals_model_name = "gpt-3.5-turbo"
    # evals_model_name = "gpt-4"  # use GPT-4 if you have access
    query_texts = query_df[":feature.text:prompt"].tolist()
    list_of_document_id_lists = query_df[":feature.[str].retrieved_document_ids:prompt"].tolist()
    document_id_to_text = dict(zip(database_df["document_id"].to_list(), database_df["text"].to_list(), strict=False))

    first_document_texts, second_document_texts = [
        [document_id_to_text[document_ids[document_index]] for document_ids in list_of_document_id_lists]
        for document_index in [0, 1]
    ]
    first_document_relevances, second_document_relevances = [
        [
            classify_relevance(query_text, document_text, evals_model_name)
            for query_text, document_text in zip(query_texts, first_document_texts, strict=False)
        ]
        for document_texts in [first_document_texts, second_document_texts]
    ]

    query_df = query_df.assign(
        retrieved_document_text_0=first_document_texts,
        retrieved_document_text_1=second_document_texts,
        relevance_0=first_document_relevances,
        relevance_1=second_document_relevances,
    )
    query_df[
        [
            ":feature.text:prompt",
            "retrieved_document_text_0",
            "retrieved_document_text_1",
            "relevance_0",
            "relevance_1",
        ]
    ].rename(columns={":feature.text:prompt": "query_text"})

    first_document_relevances = [
        {"relevant": True, "irrelevant": False}.get(rel) for rel in query_df[":tag.str:openai_relevance_0"].tolist()
    ]
    second_document_relevances = [
        {"relevant": True, "irrelevant": False}.get(rel) for rel in query_df[":tag.str:openai_relevance_1"].tolist()
    ]
    list_of_precisions_at_k_lists = [
        compute_precisions_at_k([rel0, rel1])
        for rel0, rel1 in zip(first_document_relevances, second_document_relevances, strict=False)
    ]
    precisions_at_1, precisions_at_2 = [
        [precisions_at_k[index] for precisions_at_k in list_of_precisions_at_k_lists] for index in [0, 1]
    ]
    query_df[":tag.float:openai_precision_at_1"] = precisions_at_1
    query_df[":tag.float:openai_precision_at_2"] = precisions_at_2
    query_df[
        [
            ":tag.str:openai_relevance_0",
            ":tag.str:openai_relevance_1",
            ":tag.float:openai_precision_at_1",
            ":tag.float:openai_precision_at_2",
        ]
    ]

    # get a random sample of 500 documents (including retrieved documents)
    # this will be handled by by the application in a coming release
    num_sampled_point = 500
    retrieved_document_ids = set(
        [doc_id for doc_ids in query_df[":feature.[str].retrieved_document_ids:prompt"].to_list() for doc_id in doc_ids]
    )
    retrieved_document_mask = database_df["document_id"].isin(retrieved_document_ids)
    num_retrieved_documents = len(retrieved_document_ids)
    num_additional_samples = num_sampled_point - num_retrieved_documents
    unretrieved_document_mask = ~retrieved_document_mask
    sampled_unretrieved_document_ids = set(
        database_df[unretrieved_document_mask]["document_id"].sample(n=num_additional_samples, random_state=0).to_list()
    )
    sampled_unretrieved_document_mask = database_df["document_id"].isin(sampled_unretrieved_document_ids)
    sampled_document_mask = retrieved_document_mask | sampled_unretrieved_document_mask
    sampled_database_df = database_df[sampled_document_mask]

    database_schema = px.Schema(
        prediction_id_column_name="document_id",
        prompt_column_names=px.EmbeddingColumnNames(
            vector_column_name="text_vector",
            raw_data_column_name="text",
        ),
    )
    database_ds = px.Dataset(
        dataframe=sampled_database_df,
        schema=database_schema,
        name="database",
    )

    query_ds = px.Dataset.from_open_inference(query_df)

    return database_ds, query_ds


spaces = list_shared_spaces()
selected_space = st.selectbox(
    "Space",
    spaces,
    format_func=lambda x: x[2],
    label_visibility="visible",
    index=0,
)

selected_exp_id = st.selectbox(
    "Experiment",
    list(experiments.keys()),
    format_func=lambda x: experiments[x],
    label_visibility="visible",
    index=0,
)


selected_org_id = get_selected_org_id()

space = SpaceKey(SpaceType.SHARED, selected_space[0], selected_org_id)

saved_model_settings = get_saved_model_settings_collection(selected_org_id)

trace_ds = load_phoenix_traces(space=space, exp_id=selected_exp_id)

vector_index = load_index(space, saved_model_settings)


phoenix_session = None
if px.active_session():
    phoenix_session = px.active_session()
    phoenix_session.trace_dataset = trace_ds
else:
    phoenix_session = px.launch_app(trace=trace_ds)

st.write("Phoenix URL: ", phoenix_session.url)

query_tab, vector_index_tab, graph_index_tab = st.tabs(["Query", "View Vector Index", "View Graph Index"])

with query_tab:
    input_prompt = st.text_input(label="Prompt", value="tell me more about insight engines")

    if st.button("Test entity extraction"):
        # Download from the 🤗 Hub
        from span_marker import SpanMarkerModel

        model = SpanMarkerModel.from_pretrained("tomaarsen/span-marker-mbert-base-multinerd")
        # Run inference
        entities = model.predict("Amelia Earhart flew her single engine Lockheed Vega 5B across the Atlantic to Paris.")
        entities
    if selected_exp_id == "kg_index_1":  # noqa: SIM102
        exp_id = "kg_index_1"
        if st.button("Build KG  Index"):
            docs = get_space_document_objects(space)
            sc = _get_exp_service_context(saved_model_settings)
            sc.node_parser.get_nodes_from_documents(docs)
            # kg_index = build_knowledge_graph(space, docs, saved_model_settings, exp_id)
            # save_phoenix_traces(space, exp_id, kg_index.service_context.callback_manager.handlers)

        if st.button("Query KG Index"):
            kg_index = load_knowledge_graph_from_storage(space, exp_id)
            logging.debug("Graph Store: %s", kg_index)
            response = kg_index.as_query_engine(include_text=True).query(input_prompt)
            # flush_query_buffer_into_phoenix(phoenix_session, kg_index.service_context.callback_manager.handlers)
            save_phoenix_traces(space, exp_id, kg_index.service_context.callback_manager.handlers)

            st.write(response)

    if selected_exp_id == "graph_index_1":  # noqa: SIM102
        if st.button("Build Tree Index Graph"):
            indices = build_per_doc_tree_index(
                space, get_space_document_objects(space), saved_model_settings, "graph_index_1"
            )
            build_composable_graph_from_tree_indices(space, indices, "graph_index_1")

        if st.button("Query Composable Graph"):
            # response = index_.as_query_engine(response_mode="tree_summarize", verbose=True).query(input_prompt)
            exp_id = "graph_index_1"

            try:
                graph = load_composable_graph_from_tree_indices(space, exp_id)
                response = graph.as_query_engine().query(input_prompt)
                st.write(response)
            except Exception as e:
                st.exception(e)
                # docs = get_space_document_objects(space)
                # st.write(str(len(docs)))
                # vector_index = build_summary_index(docs, saved_model_settings)
                # vector_index.storage_context.persist(persist_dir=get_exp_index_dir(space, exp_id))

    if st.button("Query Main Index"):
        # response = index_.as_query_engine(response_mode="tree_summarize", verbose=True).query(input_prompt)
        exp_id = selected_exp_id
        response = custom_query_engine(vector_index).query(input_prompt)
        # response2 = custom_query_engine(vector_index).query(input_prompt)
        # flush_query_buffer_into_phoenix(phoenix_session, vector_index.service_context.callback_manager.handlers)
        # query_ds, database_ds = t(vector_index)
        # phoenix_session = px.launch_app(trace=trace_ds, primary=query_ds, corpus=database_ds)
        save_phoenix_traces(space, exp_id, vector_index.service_context.callback_manager.handlers)
        st.write(response)

    if selected_exp_id == "summary_index_1":  # noqa: SIM102
        if st.button("Query Summary Index"):
            # response = index_.as_query_engine(response_mode="tree_summarize", verbose=True).query(input_prompt)
            exp_id = "summary_index_1"

            try:
                vector_index = load_index(space, saved_model_settings, exp_id)
            except Exception as e:
                raise e
                docs = get_space_document_objects(space)
                st.write(str(len(docs)))
                vector_index = build_summary_index(docs, saved_model_settings)
                vector_index.storage_context.persist(persist_dir=get_exp_index_dir(space, exp_id))

            response = vector_index.as_query_engine().query(input_prompt)
            st.write(response)

    if st.button("Evaluate Index"):

        async def func() -> None:
            """Evaluate index."""
            retriever = vector_index.as_retriever()
            retriever_evaluator = RetrieverEvaluator.from_metric_names(["mrr", "hit_rate"], retriever=retriever)

            # retriever_evaluator.evaluate(query="query", expected_ids=["node_id1", "node_id2"])
            from llama_index.evaluation import generate_question_context_pairs

            qa_dataset = generate_question_context_pairs(
                [n for k, n, in vector_index.docstore.docs.items()],
                llm=_get_completion_model(saved_model_settings),
                num_questions_per_chunk=2,
            )
            eval_results = await retriever_evaluator.aevaluate_dataset(qa_dataset)
            st.write(eval_results)

        asyncio.run(func())

with vector_index_tab:
    selected_doc = st.selectbox(
        f"Index Docs {str(len(vector_index.ref_doc_info))}",
        vector_index.ref_doc_info.keys(),
        label_visibility="visible",
        index=0,
    )

    st.write(vector_index.ref_doc_info.get(selected_doc))


with graph_index_tab:
    from pyvis.network import Network

    kg_index = load_knowledge_graph_from_storage(space, "kg_index_1")
    g = kg_index.get_networkx_graph()
    net = Network(notebook=True, height="900px", width="100%", cdn_resources="local")
    net.from_nx(g)
    net.show("graph_index_vis.html")
    HtmlFile = open("graph_index_vis.html", "r", encoding="utf-8")
    source_code = HtmlFile.read()
    components.html(source_code, height=900, width=900)
