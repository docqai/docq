"""sdfsdf."""
import importlib.util
import logging
import sys
from importlib.machinery import ModuleSpec

from . import extensions

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(process)d %(levelname)s %(message)s", force=True)
def load_extensions() -> None:
    """Load extensions."""
    #extensions._extensions_init()

    file_path = "../docq-extensions/source/docq_extensions/__init__.py"
    module_name = "docq_extensions"

    logging.info("start loading extensions")

    spec: ModuleSpec | None = importlib.util.spec_from_file_location(module_name, file_path)
    if spec:
      module = importlib.util.module_from_spec(spec)
      sys.modules[module_name] = module
      if spec.loader:
         logging.info("Docq extensions loaded: %s", module_name)
         spec.loader.exec_module(module)
      else:
         logging.error("spec.loader is none. cannot load module")
    else:
       logging.error("spec is none. cannot load module")

    logging.info("end loading extensions")

#load_extensions()

extensions._extensions_init()
