"""Simple node parser with async support."""
import asyncio
import logging
from doctest import debug
from typing import List, Sequence

import llama_index.async_utils as async_utils
from llama_index.callbacks.schema import CBEventType, EventPayload
from llama_index.node_parser import SimpleNodeParser
from llama_index.node_parser.node_utils import get_nodes_from_node
from llama_index.schema import BaseNode, Document, TextNode
from llama_index.utils import get_tqdm_iterable
from opentelemetry import trace

trace = trace.get_tracer(__name__)

class AsyncSimpleNodeParser(SimpleNodeParser):
    """Simple node parser with async node splitting."""

    @trace.start_as_current_span(name="AsyncSimpleNodeParser.get_nodes_from_documents")
    def get_nodes_from_documents(
        self,
        documents: Sequence[Document],
        show_progress: bool = False,
    ) -> List[BaseNode]:
        """Parse document into nodes.

        Args:
            documents (Sequence[Document]): documents to parse
            show_progress (bool): whether to show progress while parsing
        """
        with self.callback_manager.event(
            CBEventType.NODE_PARSING, payload={EventPayload.DOCUMENTS: documents}
        ) as event:
            all_nodes: List[BaseNode] = []
            documents_with_progress = get_tqdm_iterable(documents, show_progress, "Parsing documents into nodes")

            tasks = []
            for document in documents_with_progress:
                #task = asyncio.create_task(self._aget_nodes_from_node(document))
                tasks.append(self._async_get_nodes_from_node(document))

            task_results = async_utils.run_async_tasks(tasks, show_progress)
            #logging.debug("AsyncSimpleNodeParser result_nodes: %s", result_nodes)
            #TODO: these might be out of order
            all_nodes.extend([node for result_nodes in task_results for node in result_nodes]) # flatten list of lists

            if self.metadata_extractor is not None:
                logging.debug("AsyncSimpleNodeParser class name: %s, %s", self.metadata_extractor.class_name, self.metadata_extractor.__class__)
                task_results = async_utils.run_async_tasks([self.metadata_extractor.async_process_nodes(all_nodes)])
                all_nodes = [node for result_nodes in task_results for node in result_nodes] # flatten list of lists
                logging.debug("AsyncSimpleNodeParser all_nodes: %s", all_nodes)
                logging.debug("AsyncSimpleNodeParser all_nodes is instance of List[BaseNode]: %s, %s", isinstance(all_nodes, List), isinstance(all_nodes[0], BaseNode))
            event.on_end(payload={EventPayload.NODES: all_nodes})
        return all_nodes

    @trace.start_as_current_span(name="AsyncSimpleNodeParser._async_get_nodes_from_node")
    async def _async_get_nodes_from_node(self, document: Document) -> List[TextNode]:
        return get_nodes_from_node(
            document,
            self.text_splitter,
            self.include_metadata,
            include_prev_next_rel=self.include_prev_next_rel,
        )

    @classmethod
    def class_name(cls) -> str:
        """Class name."""
        return "AsyncSimpleNodeParser"
