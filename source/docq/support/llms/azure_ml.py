"""Llama Index `LLM` class implementation for LLMs hosted using Azure ML Online Endpoints."""

from typing import Any, Callable, Dict, Optional, Sequence

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
from llama_index.llms.generic_utils import completion_response_to_chat_response
from llama_index.llms.generic_utils import (
    messages_to_prompt as generic_messages_to_prompt,
)


class AzureML(CustomLLM):
    """Llama Index `LLM` class implementation for LLMs hosted using Azure ML Online Endpoints."""

    def __init__(
        self,
        endpoint_url: str,
        api_key: str,
        model: str = "llama-13b-chat",
        temperature: float = 0.1,
        max_new_tokens: int = 200,
        max_length: int = 200,
        top_p: float = 0.9,
        do_sample: bool = True,
        model_deployment_name: Optional[str] = None,
        additional_kwargs: Optional[Dict[str, Any]] = None,
        messages_to_prompt: Optional[Callable] = None,
        callback_manager: Optional[CallbackManager] = None,
    ) -> None:
        """Initialize the LLM."""
        self._client = AzureMLOnlineEndpoint(
            endpoint_url=endpoint_url, api_key=api_key, model_deployment_name=model_deployment_name
        )  # Client(api_key)
        self._model = model
        self._temperature = temperature
        self._max_new_tokens = max_new_tokens
        self._max_length = max_length
        self._top_p = top_p
        self._do_sample = do_sample
        self._additional_kwargs = additional_kwargs or {}
        self.callback_manager = callback_manager or CallbackManager([])
        self._messages_to_prompt = messages_to_prompt or generic_messages_to_prompt

    @property
    def _model_kwargs(self) -> Dict[str, Any]:
        base_kwargs = {
            "model": self._model,
            "temperature": self._temperature,
            "max_length": self._max_new_tokens,
            "top_p": self._top_p,
            "do_sample": self._do_sample,
            "max_new_tokens": self._max_new_tokens,
        }
        model_kwargs = {
            **base_kwargs,
            **self._additional_kwargs,
        }
        return model_kwargs

    @property
    def metadata(self) -> LLMMetadata:
        """Get the metadata for the LLM."""
        return LLMMetadata(
            context_window=4096,
            num_output=DEFAULT_NUM_OUTPUTS,
            is_chat_model=True,
            is_function_calling_model=True,
            model_name="llama-api",
        )

    @llm_chat_callback()
    def chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponse:
        """Chat with the LLM."""
        prompt = self._messages_to_prompt(messages)
        completion_response = self.complete(prompt, **kwargs)
        return completion_response_to_chat_response(completion_response)

    @llm_completion_callback()
    def complete(self, prompt: str, **kwargs: Any) -> CompletionResponse:
        """Complete the prompt with the LLM."""
        # self._generate_kwargs.update({"stream": False})

        input_json_dict = {
            "input_data": {
                "input_string": prompt,
                "parameters": {
                    **self._model_kwargs,
                    **kwargs,
                },
            }
        }
        response = self._client.run(input_json_dict)

        return CompletionResponse(text=response["output"], raw=response)

    @llm_completion_callback()
    def stream_complete(self, prompt: str, **kwargs: Any) -> CompletionResponseGen:
        """Stream completion of the prompt with the LLM."""
        raise NotImplementedError("stream_complete is not supported for LlamaAPI")

    @llm_chat_callback()
    def stream_chat(self, messages: Sequence[ChatMessage], **kwargs: Any) -> ChatResponseGen:
        """Stream chat with the LLM."""
        raise NotImplementedError("stream_chat is not supported for LlamaAPI")


class AzureMLOnlineEndpoint:
    """Web API Client for interacting with an model(s) hosted by an Azure ML Online Endpoint."""

    def __init__(
        self,
        endpoint_url: str,
        api_key: str,
        model_deployment_name: Optional[str] = None,
        allow_self_signed_https: Optional[bool] = False,
    ) -> None:
        """Initialize the client.

        Args:
            endpoint_url (str): The AzureML Online endpoint URL.
            api_key (str): The API key. Primary/secondary key or AMLToken can be used.
            allow_self_signed_https (bool, optional): Whether to allow self-signed certificates. Defaults to `False`.
            model_deployment_name (str, optional): The model deployment name. Used to override server-side deployment routing rules. Defaults to `None`.
        """
        self._endpoint_url = endpoint_url
        self._api_key = api_key
        self._model_deployment_name = model_deployment_name
        self._allow_self_signed_https(allow_self_signed_https)

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

    def run(self, input_data: dict[str, any]) -> str:
        """Run the model on the input.

        Args:
            input_data (str): The prompt input data. Format is dependent on what the model expects. See the Azure ML Studio Model registry for examples.

        Returns:
            str: Model response data.
        """
        import json
        import urllib.request

        # _allow_self_signed_https(false) # this line is needed if you use self-signed certificate in your scoring service.

        body = str.encode(json.dumps(input_data))

        url = self._endpoint_url  # "https://docq-endpoint.eastus.inference.ml.azure.com/score"

        api_key = self._api_key
        if not api_key:
            raise Exception(
                "Missing API key. One should be provided to invoke the endpoint. Primary/secondary key or AMLToken can be used."
            )

        headers = {
            "Content-Type": "application/json",
            "Authorization": ("Bearer " + api_key),
        }
        # The azureml-model-deployment header will force the request to go to a specific deployment.
        # When None, requests observe the endpoint traffic rules
        if self._model_deployment_name is not None:
            headers["azureml-model-deployment"] = self._model_deployment_name

        req = urllib.request.Request(url, body, headers)

        try:
            response = urllib.request.urlopen(req)

            result = response.read()
            print(result)
        except urllib.error.HTTPError as error:
            print("The request failed with status code: " + str(error.code))

            # Print the headers - they include the request ID and the timestamp, which are useful for debugging the failure
            print(error.info())
            print(error.read().decode("utf8", "ignore"))
