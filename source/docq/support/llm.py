"""Functions for utilising LLMs."""

import logging as log
import os
import traceback
from typing import List, Optional
from uu import Error

import docq
from docq.domain import SpaceKey
from docq.manage_assistants import Assistant, llama_index_chat_prompt_template_from_assistant
from docq.manage_indices import _load_index_from_storage, load_indices_from_storage
from docq.model_selection.main import (
    LLM_MODEL_COLLECTIONS,
    LlmUsageSettingsCollection,
    ModelCapability,
    ModelProvider,
    _get_service_context,
)
from docq.support.llama_index.node_post_processors import reciprocal_rank_fusion
from docq.support.llama_index.query_pipeline_components import (
    HyDEQueryTransform,
    KwargPackComponent,
    ResponseWithChatHistory,
)
from docq.support.store import get_models_dir
from llama_index.core.base.response.schema import RESPONSE_TYPE, Response
from llama_index.core.chat_engine import SimpleChatEngine
from llama_index.core.chat_engine.types import AGENT_CHAT_RESPONSE_TYPE, AgentChatResponse
from llama_index.core.indices.base import BaseIndex
from llama_index.core.llms import ChatMessage
from llama_index.core.prompts import PromptTemplate, PromptType
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.query_pipeline import (
    InputComponent,
    QueryPipeline,
)
from llama_index.core.query_pipeline.components import FnComponent

# from llama_index.core.query_pipeline.components.argpacks import KwargPackComponent
from llama_index.core.retrievers import BaseRetriever, QueryFusionRetriever
from llama_index.core.retrievers.fusion_retriever import FUSION_MODES

# load_index_from_storage
from llama_index.embeddings.huggingface_optimum import OptimumEmbedding
from llama_index.retrievers.bm25 import BM25Retriever
from opentelemetry import trace
from opentelemetry.trace import Status, StatusCode

tracer = trace.get_tracer(__name__, docq.__version_str__)


ERROR_PROMPT = """
Examine the following error and provide a simple response for the user
Example: if the error is token limit based, simply say "Sorry, your question is too long, please try again with a shorter question"
if you can't understand the error, simply say "Sorry I cannot offer any assistance on the error message"
Make sure your response is in the first person context
ERROR: {error}
"""


@tracer.start_as_current_span(name="_init_local_models")
def _init_local_models() -> None:
    """Initialize local models."""
    for model_collection in LLM_MODEL_COLLECTIONS.values():
        for model_usage_settings in model_collection.model_usage_settings.values():
            if model_usage_settings.service_instance_config.provider == ModelProvider.HUGGINGFACE_OPTIMUM_BAAI:
                model_dir = get_models_dir(model_usage_settings.service_instance_config.model_name, makedir=False)
                if not os.path.exists(model_dir):
                    model_dir = get_models_dir(model_usage_settings.service_instance_config.model_name, makedir=True)
                    OptimumEmbedding.create_and_save_optimum_model(
                        model_usage_settings.service_instance_config.model_name,
                        model_dir,
                    )




# @tracer.start_as_current_span(name="_get_async_node_parser")
# def _get_async_node_parser(model_settings_collection: ModelUsageSettingsCollection) -> AsyncSimpleNodeParser:

#     metadata_extractor = DocqMetadataExtractor(
#         extractors=[
#             #KeywordExtractor(llm=_get_chat_model_using_langchain(model_settings_collection), keywords=5),
#         ],
#         async_extractors=[
#             DocqEntityExtractor(label_entities=True, device="cpu"),
#         ]
#     )
#     #TODO: if async node parser
#     node_parser = AsyncSimpleNodeParser.from_defaults(  # SimpleNodeParser is the default when calling ServiceContext.from_defaults()

#     )

#     return node_parser




def get_hybrid_fusion_retriever_query(
    indices: List[BaseIndex], model_settings_collection: LlmUsageSettingsCollection, similarity_top_k: int = 4
) -> BaseRetriever:
    """Hybrid fusion retriever query."""
    retrievers = []
    for index in indices:
        vector_retriever = index.as_retriever(similarity_top_k=similarity_top_k)
        retrievers.append(vector_retriever)
        bm25_retriever = BM25Retriever.from_defaults(docstore=index.docstore, similarity_top_k=similarity_top_k)
        retrievers.append(bm25_retriever)

    # the default prompt doesn't return JUST the list of queries when using some none OAI models like Llama3.
    QUERY_GEN_PROMPT = (
        "You are a helpful assistant that generates multiple search queries based on a "
        "single input <query>. You only generate the queries and NO other text. "
        "Strictly DO NOT change the name of things that appear in the <query> like the name of people, companies, and products. e.g don't change 'docq' to 'docquity'"
        "Generate {num_queries} search queries, one on each line, "
        "related to the following input query:\n"
        "<query>{query}<query>\n"
        "Queries:\n"
    )
    # Create a FusionRetriever to merge and rerank the results
    fusion_retriever = QueryFusionRetriever(
        retrievers,
        similarity_top_k=4,
        num_queries=4,  # set this to 1 to disable query generation
        mode=FUSION_MODES.RECIPROCAL_RANK,
        use_async=False,
        verbose=True,
        llm=_get_service_context(model_settings_collection).llm,
        callback_manager=_get_service_context(model_settings_collection).callback_manager,
        query_gen_prompt=QUERY_GEN_PROMPT,  # we could override the query generation prompt here
    )
    return fusion_retriever


@tracer.start_as_current_span(name="run_chat")
def run_chat(
    input_: str, history: List[ChatMessage], model_settings_collection: LlmUsageSettingsCollection, assistant: Assistant
) -> AgentChatResponse:
    """Chat directly with a LLM with history."""
    ## chat engine handles tracking the history.
    log.debug("chat assistant: ", assistant.system_message_content)

    engine = SimpleChatEngine.from_defaults(
        service_context=_get_service_context(model_settings_collection),
        kwargs=model_settings_collection.model_usage_settings[ModelCapability.CHAT].additional_args,
        system_prompt=assistant.system_message_content,
        chat_history=history,
    )
    output = engine.chat(input_)

    # log.debug("(Chat) Q: %s, A: %s", input_, output)
    return output


def run_ask(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: list[SpaceKey] | None = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    return run_ask2(input_, history, model_settings_collection, assistant, spaces)


@tracer.start_as_current_span(name="run_ask")
def run_ask1(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: Optional[list[SpaceKey]] = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    """Ask questions against existing index(es) with history."""
    log.debug("exec: runs_ask()")
    span = trace.get_current_span()

    if spaces is not None and len(spaces) > 0:
        span.set_attribute("spaces_count", len(spaces))
        log.debug("runs_ask(): spaces count: %s", len(spaces))
        # With additional spaces likely to be combining a number of shared spaces.
        indices = []
        # summaries = []
        output = _default_response()
        for s_ in spaces:
            try:
                index_ = _load_index_from_storage(s_, model_settings_collection)

                log.debug("run_chat(): %s, %s", index_.index_id, s_.summary)
                indices.append(index_)
                span.add_event(
                    name="index_appended",
                    attributes={"index_id": index_.index_id, "index_struct_cls": index_.index_struct_cls.__name__},
                )
                # s_text = s_.summary if s_.summary else ""
                # # s_text = index_.as_query_engine().query("What is a summary of this document?", )
                # summaries.append(s_text)
                # span.add_event(name="summary_appended", attributes={"index_summary": s_text})
            except Exception as e:
                span.set_status(status=Status(StatusCode.ERROR))
                span.record_exception(e)
                log.warning(
                    "Index for space '%s' failed to load, skipping. Maybe the index isn't created yet. Error message: %s",
                    s_,
                    e,
                )
                continue

        try:
            text_qa_template = llama_index_chat_prompt_template_from_assistant(assistant, history)
            span.add_event(name="prompt_created")
        except Exception as e:
            raise Error(f"Error: {e}") from e

        try:
            retriever = get_hybrid_fusion_retriever_query(indices, model_settings_collection)
            span.add_event(name="retriever_object_created", attributes={"retriever": retriever.__class__.__name__})

            query_engine = RetrieverQueryEngine.from_args(
                retriever,
                service_context=_get_service_context(model_settings_collection),
                text_qa_template=text_qa_template,
            )
            span.add_event(name="query_engine__object_created")

            output = query_engine.query(input_)
            span.add_event(name="query_executed")
        except Exception as e:
            span.set_status(status=Status(StatusCode.ERROR))
            span.record_exception(e)
            raise Error(f"Error: {e}") from e

    else:
        span.set_attribute("spaces_count", 0)
        log.debug("runs_ask(): space None or zero.")
        # No additional spaces i.e. likely to be against a user's documents in their personal space.

        output = Response("You need to select a Space or upload a document to ask a questions.")
        span.add_event(name="ask_without_spaces", attributes={"question": input_, "answer": str(output)})

    return output


@tracer.start_as_current_span(name="run_ask2")
def run_ask2(
    input_: str,
    history: List[ChatMessage],
    model_settings_collection: LlmUsageSettingsCollection,
    assistant: Assistant,
    spaces: Optional[list[SpaceKey]] = None,
) -> RESPONSE_TYPE | AGENT_CHAT_RESPONSE_TYPE:
    """Implements logic of run_ask() using LlamaIndex query pipelines."""
    span = trace.get_current_span()

    service_context = _get_service_context(model_settings_collection)
    span.add_event(name="service_context_loaded")

    try:
        indices = []
        if spaces is not None and len(spaces) > 0:
            indices = load_indices_from_storage(spaces, model_settings_collection)
            if indices is None or len(indices) == 0:
                span.add_event(name="indices_loading_failed")
                span.set_status(status=Status(StatusCode.ERROR))
                raise Error("Failed to load indices from storage for any Spaces.")

            else:
                span.add_event(
                    name="indices_loaded",
                    attributes={"num_indices_loaded": len(indices), "num_spaces_given": len(spaces)},
                )
        # text_qa_template = llama_index_chat_prompt_template_from_assistant(assistant, history)
        # span.add_event(name="prompt_created")

        similarity_top_k = 6
        span.set_attributes(
            attributes={
                "model_settings_collection": str(model_settings_collection),
                "assistant": str(assistant),
                "similarity_top_k": similarity_top_k,
            }
        )
        # print("indices:", len(indices))
        # TODO: adjust ask2 to work with multiple spaces.
        vector_retriever = indices[0].as_retriever(similarity_top_k=similarity_top_k)
        span.add_event(
            name="vector_retriever_object_created",
            attributes={
                "retriever": vector_retriever.__class__.__name__,
                "index_id": indices[0].index_id,
                "index_struct_cls": indices[0].index_struct_cls.__name__,
                "similarity_top_k": similarity_top_k,
            },
        )
        # retriever = get_hybrid_fusion_retriever_query(indices, model_settings_collection)
        if not indices[0].docstore:
            raise ValueError("The docstore is empty, cannot create BM25Retriever")

        bm25_retriever = BM25Retriever.from_defaults(docstore=indices[0].docstore, similarity_top_k=similarity_top_k)
        span.add_event(
            name="bm25_retriever_object_created",
            attributes={
                "retriever": bm25_retriever.__class__.__name__,
                "index_id": indices[0].index_id,
                "index_struct_cls": indices[0].index_struct_cls.__name__,
                "similarity_top_k": similarity_top_k,
            },
        )

        # query_engine = RetrieverQueryEngine.from_args(
        #     retriever=retriever,
        #     service_context=_get_service_context(model_settings_collection),
        #     text_qa_template=text_qa_template,
        # )
        # span.add_event(name="query_engine__object_created")

        # output = query_engine.query(input_)
        # span.add_event(name="query_executed")
    except Exception as e:
        span.set_status(status=Status(StatusCode.ERROR))
        span.record_exception(e)
        traceback.print_exc()

        raise Error(f"Error: {e}") from e

    llm = service_context.llm

    # First, we create an input component to capture the user query
    input_component = InputComponent()
    span.add_event(name="query_pipeline_declaration_start")
    span.add_event(name="input_component_created")

    # Next, we use the LLM to rewrite a user query
    HYDE_TMPL = (
        "Please write a passage to answer the <question>\n"
        "Use the current conversation available in <chat_history>\n"
        "Try to include as many key details as possible.\n"
        "\n"
        "<chat_history_str>\n"
        "{chat_history_str}\n"
        "</chat_history_str>\n"
        "<question>\n"
        "{query_str}\n"
        "</question>\n"
        "\n"
        "\n"
        'Passage:"""\n'
    )
    history_str = "\n".join([str(x) for x in history])
    hyde_template = PromptTemplate(template=HYDE_TMPL, prompt_type=PromptType.SUMMARY)
    span.add_event(name="hyde_prompt_template_created", attributes={"template": str(hyde_template)})
    hyde_query_transform_component = HyDEQueryTransform(
        llm=llm, hyde_prompt=hyde_template, prompt_args={"chat_history_str": history_str}
    ).as_query_component()

    span.add_event(name="hyde_query_transform_component_created")

    # we will retrieve two times, so we need to pack the retrieved nodes into a single list
    # argpack_component = ArgPackComponent()
    kwargpack_component = KwargPackComponent()
    span.add_event(name="kwargpack_component_created")

    rerank_component = FnComponent(fn=reciprocal_rank_fusion)
    span.add_event(name="rerank_component_created")

    response_component = ResponseWithChatHistory(
        llm=llm,
        system_prompt=assistant.system_message_content,
    )
    span.add_event(name="response_component_created")

    # define query pipeline
    pipeline = QueryPipeline(
        modules={
            "input": input_component,
            "hyde_query_transform": hyde_query_transform_component,
            "v_rewrite_retriever": vector_retriever,
            "v_query_retriever": vector_retriever,
            # "bm25_rewrite_retriever": bm25_retriever,
            "bm25_query_retriever": bm25_retriever,
            "join": kwargpack_component,
            "RRF_reranker": rerank_component,
            "response_component": response_component,
        },
        verbose=False,
    )
    span.add_event(name="query_pipeline_definition_created")

    # transform the user query using the HyDE technique
    pipeline.add_link("input", "hyde_query_transform", src_key="query_str", dest_key="query_str")

    # run multiple retrievals (note we don't do BM25 with the hallucinated query. in a new thread it doesn't make sense)
    pipeline.add_link(
        "hyde_query_transform", "v_rewrite_retriever"
    )  # vector search with the *hallucinated* query (HyDE)
    pipeline.add_link("input", "v_query_retriever", src_key="query_str")  # vector search with the *original* query
    pipeline.add_link("input", "bm25_query_retriever", src_key="query_str")  # BM25 search with the *original* query

    # each input to the Kwargpack component needs a dest key -- it's the key on the dict so can be anything.
    # then, the kwargpack component will pack all the inputs into a dict of lists of nodes called 'join'. It's intentionally this for RRF rerank algo to work.
    pipeline.add_link("v_rewrite_retriever", "join", dest_key="v_rewrite_nodes")
    pipeline.add_link("v_query_retriever", "join", dest_key="v_query_nodes")
    pipeline.add_link("bm25_query_retriever", "join", dest_key="bm25_query_nodes")

    # RRF reranker needs the packed dict of node list from each retrieval
    # TODO: add top k
    pipeline.add_link("join", "RRF_reranker", src_key="output", dest_key="results")

    # synthesizer needs the reranked nodes,  query str, and chat history
    pipeline.add_link("RRF_reranker", "response_component", dest_key="nodes")
    pipeline.add_link("input", "response_component", src_key="query_str", dest_key="query_str")
    pipeline.add_link(
        "input",
        "response_component",
        src_key="chat_history",
        dest_key="chat_history",
    )
    span.add_event(name="query_pipeline_all_links_created")
    span.add_event(name="query_pipeline_declaration_end")
    # from pyvis.network import Network # -- poetry add pyvis

    # net = Network(notebook=True, cdn_resources="in_line", directed=True)
    # net.from_nx(pipeline.dag)
    # net.show("web/rag_dag.html")

    # output, intermediates = pipeline.run_with_intermediates(input_)

    span.add_event(name="query_pipeline_execution_started")
    output, intermediates = pipeline.run_with_intermediates(
        query_str=input_,
        chat_history=history,
        chat_history_str=history_str,
        callback_manager=service_context.callback_manager,
    )
    span.add_event(name="query_pipeline_execution_finished")

    # # debug code
    # for k, v in intermediates.items():
    #     print(f"{AnsiColours.BLUE.value}>>{k}{AnsiColours.RESET.value}:")
    #     for ki, vi in v.inputs.items():
    #         print(
    #             f"{AnsiColours.GREEN.value}>>>>in: {ki} ({type(vi).__name__}) value: {len(vi)} {AnsiColours.RESET.value}"
    #         )

    #     for ko, vo in v.outputs.items():
    #         if not isinstance(vo, ChatResponse):
    #             print(
    #                 f"{AnsiColours.GREEN.value}>>>>out: {ko} ({type(vo).__name__}) value:   {len(vo)} {AnsiColours.RESET.value}"
    #             )
    #         else:
    #             print(f"{AnsiColours.GREEN.value}>>>>out: {ko} ({type(vo).__name__})  {AnsiColours.RESET.value}")
    #         # if k == "join":

    # print("ANSWER:", output.get("response", "blah!").message)

    return Response(
        response=output.get("response", "blah!").message.content, source_nodes=output.get("source_nodes", [])
    )


@tracer.start_as_current_span(name="_default_response")
def _default_response() -> Response:
    """A default response incase of any failure."""
    return Response("I don't know.")


@tracer.start_as_current_span(name="query_error")
def query_error(error: Exception, model_settings_collection: LlmUsageSettingsCollection) -> Response:
    """Query for a response to an error message."""
    try:  # Try re-prompting with the AI
        log.exception("Error: %s", error)
        input_ = ERROR_PROMPT.format(error=error)
        return SimpleChatEngine.from_defaults(service_context=_get_service_context(model_settings_collection)).chat(
            input_
        )
    except Exception as error:
        log.exception("Error: %s", error)
        return _default_response()
