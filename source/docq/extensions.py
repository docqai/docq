"""Interfaces for extensions to DocQ."""
import importlib
import importlib.util
import json
import logging
import os
import sys
from abc import ABC, abstractmethod
from dataclasses import dataclass
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Optional, Self, Type

from opentelemetry import trace

import docq

from .support import store

tracer = trace.get_tracer(__name__, docq.__version_str__)


@dataclass
class ExtensionContext:
    """Context for an extension."""
    extension_register: Optional[dict] = None
    """A reference to the instances of Docq extensions registered at startup. This dictionary is keyed by the extension `class_name()`."""
    data: Optional[dict] = None
    """Event specific context data passed to all callback handlers."""
    web_components: Optional[dict] = None
    """A reference to instances of web components of the Docq application. For example `st.container` or `st.tab` so the extension can add to the UI."""


class DocqExtension(ABC):
    """Base class for all DocQ extensions."""

    @classmethod
    @abstractmethod
    def class_name(cls: Type['DocqExtension']) -> str:
        """Return the name of the class."""
        pass


    @abstractmethod
    def callback_handler(self: Self, event_name: str, _context: ExtensionContext) -> None:
        """Callback handler for the extension.

        Args:
            event_name: The name of the event. format <webui|webapi|dal><thing>.<action as past tense verb> TODO: design and define these well and represent in some structure like an enum.
            _context: The context of the event. TODO: this need structure to be designed. probably need several classes of contexts for different scenarios.
        """
        pass

class DocqWebUiExtension(DocqExtension):
    """Interface for extensions to the DocQ Web UI."""
    pass


class DocqWebApiExtension(DocqExtension):
    """Interface for extensions to the DocQ Web API."""
    pass


class DocqDalExtension(DocqExtension):
    """Interface for extensions to the DocQ Data Access Layer."""
    def __init__(self: Self, sqlite_system_file_path: str) -> None:
        """Initialise the database."""
        self.sqlite_system_file_path = sqlite_system_file_path
        #self.sqlite_usage_file_path = sqlite_usage_file_path
        self._init_database()

    @abstractmethod
    def _init_database(self: Self) -> None:
        """Initialise the database."""
        pass




DEFAULT_EXTENSION_JSON_PATH =  os.path.join(Path(__file__).cwd(), ".docq-extensions.json")

_registered_extensions: dict[str, DocqExtension] = {}

@tracer.start_as_current_span("_import_extensions")
def _import_extensions(extensions_config_path: str = DEFAULT_EXTENSION_JSON_PATH) -> list[type[DocqExtension]]:
    """Import or download extension modules.

    Args:
        extensions_config_path: Path to a docq-extensions.json config file.

    Returns:
        The extension module.
    """
    extension_cls: list[type[DocqExtension]] = []
    path = extensions_config_path
    extension_config_exists = os.path.exists(path)
    span = trace.get_current_span()
    span.add_event("extension_config_exists checked", {"extension_config_exists": extension_config_exists})
    if extension_config_exists:
        try:
            with open(file=path, mode="r") as f:
                extensions_json = json.load(f)
                for key in extensions_json:
                    module_name = str(extensions_json[key]["module_name"])
                    module_source = str(extensions_json[key]["source"])
                    class_name = str(extensions_json[key]["class_name"]) if "class_name" in extensions_json[key] else None

                    span.add_event("extension importlib.util.spec_from_file_location starting", {"module_name": module_name, "module_source": module_source, "class_name": class_name})
                    _spec: ModuleSpec | None = importlib.util.spec_from_file_location(module_name, module_source)
                    if _spec:
                        module = importlib.util.module_from_spec(_spec)
                        sys.modules[module_name] = module
                        if _spec.loader:
                            _spec.loader.exec_module(module)
                            span.add_event("extension module loaded", {"module_name": module_name, "module_source": module_source, "class_name": class_name})
                            if class_name:
                                extension_cls.append(getattr(module, class_name))
                                #span.add_event("extension class registered", {"module_name": module_name, "module_source": module_source, "class_name": class_name})
                        else:
                            span.add_event("extension module load failed", {"module_name": module_name, "module_source": module_source, "class_name": class_name})
                            raise Exception(f"Could not load extension module '{module_name}' at '{module_source}'")
                    else:
                        span.add_event("importlib.spec_from_file_location() for extension failed", {"module_name": module_name, "module_source": module_source, "class_name": class_name})
                        logging.error("importlib.spec_from_file_location() for extension failed. Skipping... could not find extension module '%s' at '%s'.", module_name, module_source)
        except Exception as e:
            span.set_status(status=trace.StatusCode.ERROR, description=str(e))
            logging.error("_import_extensions() failed hard!")
            logging.error(e)
            raise e

    return extension_cls

def register_extensions(extension_classes: list[type[DocqExtension]]) -> None:
    """Register callback handlers for all registered extensions."""
    for cls in extension_classes:
        if issubclass(cls, DocqWebUiExtension):
            _registered_extensions[cls.class_name()] = cls()
        elif issubclass(cls, DocqDalExtension):
            _registered_extensions[cls.class_name()] = cls(sqlite_system_file_path=store.get_sqlite_system_file())
        elif issubclass(cls, DocqWebApiExtension):
            _registered_extensions[cls.class_name()] = cls()

def _extensions_init() -> None:
    """Register extensions."""
    extensions_classes = _import_extensions()
    logging.info("extension classes: %s", extensions_classes)
    register_extensions(extensions_classes)
    logging.info("Imported %s extension classes", len(extensions_classes))
    logging.info("Registered %s extension(s).",len(_registered_extensions.keys()))
    if len(extensions_classes) != len(_registered_extensions.keys()):
        logging.error("Imported extension classes count is not equal to registered extension count. Something went wrong.")
        logging.debug(_registered_extensions.keys())
