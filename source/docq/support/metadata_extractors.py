"""Custom metadata extractors for Llama Index.

Metadata extractors for nodes. Applied as a post processor to node parsing.
Currently, only `TextNode` is supported.

Supported metadata:
Node-level:
    - `SummaryExtractor`: Summary of each node, and pre and post nodes
    - `QuestionsAnsweredExtractor`: Questions that the node can answer
    - `KeywordsExtractor`: Keywords that uniquely identify the node
Document-level:
    - `TitleExtractor`: Document title, possible inferred across multiple nodes

Unimplemented (contributions welcome):
Subsection:
    - Position of node in subsection hierarchy (and associated subtitles)
    - Hierarchically organized summary

The prompts used to generate the metadata are specifically aimed to help
disambiguate the document or subsection from other similar documents or subsections.
(similar with contrastive learning)
"""

# Forked from 'llama_index/llama_index/node_parser/extractors/metadata_extractors.py'
# The MIT License
# Copyright (c) Jerry Liu
# For full license see https://github.com/run-llama/llama_index/blob/main/LICENSE

import logging
import os
from typing import Any, Callable, Dict, List, Optional, Sequence
from .store import get_models_dir
from llama_index.node_parser.extractors.metadata_extractors import MetadataFeatureExtractor
from pydantic import Field, PrivateAttr
from llama_index.schema import BaseNode


DEFAULT_EXTRACT_TEMPLATE_STR = """\
Here is the content of the section:
----------------
{context_str}
----------------
Given the contextual information, extract out a {class_name} object.\
"""

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

DEFAULT_MODEL_PATH = get_models_dir(DEFAULT_ENTITY_MODEL, makedir=False)


def _cache_metadata_extractor_models() -> None:
    """Cache metadata extractor models."""

    # cache default model
    dir_ = get_models_dir(DEFAULT_ENTITY_MODEL, makedir=False)
    if not os.path.exists(dir_):
        logging.info("Caching default DocqEntityExtractor model: '%s'", DEFAULT_ENTITY_MODEL)
        DocqEntityExtractor.save_model(path=dir_)


class DocqEntityExtractor(MetadataFeatureExtractor):
    """Entity extractor. Extracts `entities` into a metadata field using a default model `tomaarsen/span-marker-mbert-base-multinerd` and the SpanMarker library.

    Install SpanMarker with `pip install span-marker`.
    """

    model_name: str = Field(
        default=DEFAULT_ENTITY_MODEL,
        description="The model name of the SpanMarker model to use.",
    )
    model_path: str = Field(
        default=DEFAULT_MODEL_PATH,
        description="The path to load the model from if already saved by calling EntityExtractor.save_model().",
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
        model_path: str = DEFAULT_MODEL_PATH,
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
            model_path (Optional[str]):
                Path to load the model from if already saved by calling EntityExtractor.save_model(). Defaults to None (which will load the model from the default model hub.)
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
            raise ImportError("SpanMarker is not installed. Install with `poetry add span-marker`.") from err

        try:
            from nltk.tokenize import word_tokenize
        except ImportError:
            raise ImportError("NLTK is not installed. Install with `poetry add nltk`.")

        if not os.path.exists(model_path):
            logging.info("EntityExtractor loading and caching model: '%s'", model_name)
            self._model = SpanMarkerModel.from_pretrained(model_name)
            self._model.save_pretrained(model_path)
        else:
            try:
                self._model = SpanMarkerModel.from_pretrained(model_path)
                logging.info("EntityExtractor loaded model from cache path: '%s'", model_path)
            except Exception as e:
                raise Exception(
                    f"Loading EntityExtractor model from path '{model_path}' failed. Maybe save_model() wasn't called or the path is invalid."
                ) from e

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

    def save_model(model_name: str = DEFAULT_ENTITY_MODEL, path: str = DEFAULT_MODEL_PATH) -> None:
        """Save model to path and cache it."""
        try:
            from span_marker import SpanMarkerModel
        except ImportError as err:
            raise ImportError("SpanMarker is not installed. Install with `poetry add span-marker`.") from err

        SpanMarkerModel.from_pretrained(model_name).save_pretrained(save_directory=path)

    def extract(self, nodes: Sequence[BaseNode]) -> List[Dict]:
        """Extract node-level entity metadata."""
        metadata_list: List[Dict] = [{} for _ in nodes]
        node_count = len(nodes)
        for i, metadata in enumerate(metadata_list):
            node_text = nodes[i].get_content(metadata_mode=self.metadata_mode)
            words = self._tokenizer(node_text)
            spans = self._model.predict(words)
            logging.debug("EntityExtractor: processed node %s of %s: %s", i, node_count, nodes[i].hash)
            logging.debug("EntityExtractor: node text: %s", node_text)
            # spans = self._model.predict(node_text)
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
        logging.debug("EntityExtractor: %s", metadata_list)
        return metadata_list
