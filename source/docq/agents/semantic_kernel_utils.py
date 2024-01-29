"""Utils that help using Semantic Kernel plugins, and therefore OpenAI plugins, with AutoGen."""

import datetime
from typing import Any, Callable, Dict, List, Self

import semantic_kernel as sk
from opentelemetry import trace

from ..model_selection.main import LlmUsageSettings

tracer = trace.get_tracer(__name__)

ASSISTANT_PERSONA = f"""Only use the functions you have been provided with.
Do not ask the user to perform other actions than executing the functions.
Use the functions you have to find information not available.
Present the final answer or result in a clear, concise and easy to understand way.
Today's date is: {datetime.date.today().strftime("%B %d, %Y")}.
Reply TERMINATE when the task is done.
"""

def generate_autogen_llm_config(chat_model_settings: LlmUsageSettings, kernel: sk.Kernel) -> Dict:
    """Generate an AutoGen LLM config, with function call definitions, from Docq Model Settings."""
    sc = chat_model_settings.service_instance_config
    return {
        "function_call": "auto",
        "functions": get_oai_function_definitions(kernel),
        "config_list": [{
            "model": sc.model_deployment_name.__str__(),
            "api_key":  sc.api_key or "",
            "base_url": sc.api_base or "",
            "api_type": sc.api_type or "azure",
            "api_version": "2023-07-01-preview" #"2023-10-01-preview",
        }],
    }

def get_oai_function_definitions(kernel: sk.Kernel) -> List:
    """Get the list of function definitions for OpenAI Function Calling.

    Usage:
      ```json
      llm_config = {
        "function_call": "auto",
        "functions": get_oai_function_definitions(kernel)
        "config_list": [utils.get_autogen_llm_config(chat_model_settings)]
      }
      ```
    """
    functions = []
    sk_functions = kernel.skills.get_functions_view()
    for ns in {**sk_functions.native_functions, **sk_functions.semantic_functions}:
        for f in sk_functions.native_functions[ns]:
            functions.append(
                {
                    "name": f.name,
                    "description": f.description,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            p.name: {"description": p.description, "type": p.type_} for p in f.parameters
                        },
                        "required": [p.name for p in f.parameters],
                    },
                }
            )
    return functions

def get_autogen_function_map(kernel: sk.Kernel) -> Dict:
    """Convert SK functions to a a AutoGen function map. Passed in directly to `function_map` argument of the Agent constructor."""
    function_map = {}
    sk_functions = kernel.skills.get_functions_view()
    for ns in {**sk_functions.native_functions, **sk_functions.semantic_functions}:
        for f in sk_functions.native_functions[ns]:
            function_map[f.name] = SemanticKernelFunctionWrapper(
                kernel.skills.get_function(f.skill_name, f.name) # type: ignore
            )
    return function_map


class SemanticKernelFunctionWrapper:
    """Wrapper for SK functions to be used with AutoGen Function Calling."""

    _function: Callable[..., str]

    def __init__(self: Self, delegate_function: Callable):
        """Create a new SKFunctionWrapper."""
        self._function = delegate_function

    def __call__(self: Self, **kwargs: Dict[str, Any]) -> str:
        """Call the wrapped function."""
        with tracer.start_as_current_span("SemanticKernelFunctionWrapper.__call__") as span:
            variables = sk.ContextVariables()
            for k, v in kwargs.items():
                variables[k] = str(v)
            span.set_attribute("kwargs", kwargs.__str__())
            span.set_attribute("sk.ContextVariables", variables.__str__())
            return self._function(variables=variables)
