"""Interfaces for extensions to DocQ."""
import importlib
import importlib.util
import json
import logging
import os
from abc import ABC, abstractmethod
from importlib.machinery import ModuleSpec
from pathlib import Path
from typing import Any, List, Optional, Self, Type


class DocqExtension(ABC):
    """Base class for all DocQ extensions."""

    @classmethod
    @abstractmethod
    def class_name(cls: Type['DocqExtension']) -> str:
        """Return the name of the class."""
        pass


    @abstractmethod
    def callback_handler(self: Self, event_name: str, _context: Any) -> None:
        """Callback handler for the extension."""
        pass



class DocqWebUiExtension(DocqExtension):
    """Interface for extensions to the DocQ Web UI."""
    pass


class DocqWebApiExtension(DocqExtension):
    """Interface for extensions to the DocQ Web API."""
    pass


class DocqDalExtension(DocqExtension):
    """Interface for extensions to the DocQ Data Access Layer."""
    pass


DEFAULT_EXTENSION_JSON_PATH =  os.path.join(Path(__file__).cwd(), "docq-extensions.json")

_registered_extensions: List[DocqExtension] = []


def _import_extensions(extensions_config_path: Optional[str] = DEFAULT_EXTENSION_JSON_PATH) -> list[Type[DocqExtension]]:
    """Import or download extension modules.

    Args:
        extensions_config_path: Path to a docq-extensions.json config file.

    Returns:
        The extension module.
    """
    extension_cls: list[Type[DocqExtension]] = []
    path = extensions_config_path
    
    try:
        with open(path, "r") as f:
            extensions_json = json.load(f)
            for key in extensions_json:
                module_name = str(extensions_json[key]["module_name"])
                module_source = str(extensions_json[key]["source"])
                class_name = str(extensions_json[key]["class_name"])

                _spec: ModuleSpec | None = importlib.util.spec_from_file_location(module_name, module_source)
                if _spec:
                    module = importlib.util.module_from_spec(_spec)
                    if _spec.loader:
                        _spec.loader.exec_module(module)
                        extension_cls.append(getattr(module, class_name))
                    else:
                        raise Exception(f"Could not load extension module '{module_name}' at '{module_source}'")
                else:
                    logging.error("Error loading extension. Skipping... could not find extension module '%s' at '%s'.", module_name, module_source)
    except Exception as e:
        logging.error("_import_extensions() failed hard!")
        logging.error(e)
        raise e

    return extension_cls

def register_extensions(extension_classes: list[Type[DocqExtension]]) -> None:
    """Register callback handlers for all registered extensions."""
    for cls in extension_classes:
        _registered_extensions.append(cls())

def _extensions_init() -> None:
    """Register extensions."""
    extensions_classes = _import_extensions()
    register_extensions(extensions_classes)
    logging.info("Registered %s extension(s).",len(extensions_classes))
