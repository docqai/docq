"""Llama Index `LLM` class implementation for LLMs hosted using Azure ML Online Endpoints."""

from typing import Any, Dict, Optional, Sequence

from llama_index.callbacks import CallbackManager
from llama_index.constants import DEFAULT_NUM_OUTPUTS
from llama_index.llms.base import (
    ChatMessage,
    ChatResponse,
    ChatResponseGen,
    CompletionResponse,
    CompletionResponseGen,
    LLMMetadata,
    llm_chat_callback,
    llm_completion_callback,
)
from llama_index.llms.custom import CustomLLM
from llama_index.llms.generic_utils import chat_to_completion_decorator
from llama_index.llms.openai_utils import (
    from_openai_message_dict,
    to_openai_message_dicts,
)


class AzureML(CustomLLM):
    """Llama Index `LLM` class implementation for LLMs hosted using Azure ML Online Endpoints."""

    def __init__(
        self,
        endpoint_url: str,
        api_key: str,
        model: str = "llama-13b-chat",
        temperature: float = 0.1,
        max_length: int = 200,
        max_tokens: int = 200,
        top_p: float = 0.9,
        do_sample: bool = True,
        additional_kwargs: Optional[Dict[str, Any]] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        try:
            from llamaapi import LlamaAPI as Client
        except ImportError as e:
            raise ImportError("llama_api not installed." "Please install it with `pip install llamaapi`.") from e

        self._client = Client(api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens
        self._additional_kwargs = additional_kwargs or {}
        self.callback_manager = callback_manager or CallbackManager([])

    @property
    def _model_kwargs(self) -> Dict[str, Any]:
        base_kwargs = {
            "model": self._model,
            "temperature": self._temperature,
            "max_length": self._max_tokens,
        }
        model_kwargs = {
            **base_kwargs,
            **self._additional_kwargs,
        }
        return model_kwargs

    @property
    def metadata(self) -> LLMMetadata:
        return LLMMetadata(
            context_window=4096,
            num_output=DEFAULT_NUM_OUTPUTS,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name="llama-api",
        )

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        message_dicts = to_openai_message_dicts(messages)
        json_dict = {
            "messages": message_dicts,
            **self._model_kwargs,
            **kwargs,
        }
        response = self._client.run(json_dict).json()
        message_dict = response["choices"][0]["message"]
        message = from_openai_message_dict(message_dict)

        return ChatResponse(message=message, raw=response)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        complete_fn = chat_to_completion_decorator(self.chat)
        return complete_fn(prompt, **kwargs)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        raise NotImplementedError("stream_complete is not supported for LlamaAPI")

    @llm_chat_callback()
    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        raise NotImplementedError("stream_chat is not supported for LlamaAPI")

    def _allow_self_signed_https(self, allowed: bool) -> None:
        """Bypass the server certificate verification on client side if using self-signed certificate in your scoring service aka Azure Online endpoint.

        You would only use a self-signed certificate when running a local endpoint for dev and testing purposes.

        Args:
            allowed (bool): Whether to allow self-signed certificates.
        """
        import os
        import ssl

        if allowed and not os.environ.get("PYTHONHTTPSVERIFY", "") and getattr(ssl, "_create_unverified_context", None):
            ssl._create_default_https_context = ssl._create_unverified_context

    def _azureml_request(self, input: str) -> None:
        import json
        import urllib.request

        # _allow_self_signed_https(false) # this line is needed if you use self-signed certificate in your scoring service.

        # Request data goes here
        # The example below assumes JSON formatting which may be updated
        # depending on the format your endpoint expects.
        # More information can be found here:
        # https://docs.microsoft.com/azure/machine-learning/how-to-deploy-advanced-entry-script
        data = {}

        body = str.encode(json.dumps(data))

        url = "https://docq-endpoint.eastus.inference.ml.azure.com/score"
        # Replace this with the primary/secondary key or AMLToken for the endpoint
        api_key = ""
        if not api_key:
            raise Exception("A key should be provided to invoke the endpoint")

        # The azureml-model-deployment header will force the request to go to a specific deployment.
        # Remove this header to have the request observe the endpoint traffic rules
        headers = {
            "Content-Type": "application/json",
            "Authorization": ("Bearer " + api_key),
            "azureml-model-deployment": "llama2-7b-chat-8",
        }

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            print(result)
        except urllib.error.HTTPError as error:
            print("The request failed with status code: " + str(error.code))

            # Print the headers - they include the requert ID and the timestamp, which are useful for debugging the failure
            print(error.info())
            print(error.read().decode("utf8", "ignore"))
