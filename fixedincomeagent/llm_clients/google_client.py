from typing import Any

from google.genai.errors import APIError as ServerError, ClientError
from langchain_core.callbacks import AsyncCallbackManagerForLLMRun, CallbackManagerForLLMRun
from langchain_core.messages import BaseMessage
from langchain_core.outputs import ChatResult
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai.chat_models import (
    _handle_client_error,
    _handle_server_error,
    _response_to_result,
)

from .base_client import BaseLLMClient, normalize_content
from .validators import validate_model


class NormalizedChatGoogleGenerativeAI(ChatGoogleGenerativeAI):
    """ChatGoogleGenerativeAI with normalized content output.

    Gemini 3 models return content as list of typed blocks.
    This normalizes to string for consistent downstream handling.
    Overrides _generate and _agenerate to route execution through
    the Chat API (chats.create + send_message) instead of models.generate_content,
    preventing Automatic Function Calling (AFC) deprecation warnings.
    """

    def _generate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: CallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.client is None:
            msg = "Client not initialized."
            raise ValueError(msg)

        if "cached_content" not in kwargs and self.cached_content:
            kwargs["cached_content"] = self.cached_content

        request = self._prepare_request(messages, stop=stop, **kwargs)

        model = request.get("model")
        contents = request.get("contents")
        config = request.get("config")

        history = contents[:-1] if contents and len(contents) > 1 else None
        if contents:
            last = contents[-1]
            last_message = last.parts if hasattr(last, "parts") else last
        else:
            last_message = ""

        try:
            chat = self.client.chats.create(model=model, config=config, history=history)
            response = chat.send_message(last_message)
        except ClientError as e:
            _handle_client_error(e, request)
        except ServerError as e:
            _handle_server_error(e)

        return _response_to_result(response)

    async def _agenerate(
        self,
        messages: list[BaseMessage],
        stop: list[str] | None = None,
        run_manager: AsyncCallbackManagerForLLMRun | None = None,
        **kwargs: Any,
    ) -> ChatResult:
        if self.client is None:
            msg = "Client not initialized."
            raise ValueError(msg)

        if "cached_content" not in kwargs and self.cached_content:
            kwargs["cached_content"] = self.cached_content

        request = self._prepare_request(messages, stop=stop, **kwargs)

        model = request.get("model")
        contents = request.get("contents")
        config = request.get("config")

        history = contents[:-1] if contents and len(contents) > 1 else None
        if contents:
            last = contents[-1]
            last_message = last.parts if hasattr(last, "parts") else last
        else:
            last_message = ""

        try:
            chat = self.async_client.chats.create(model=model, config=config, history=history)
            response = await chat.send_message(last_message)
        except ClientError as e:
            _handle_client_error(e, request)
        except ServerError as e:
            _handle_server_error(e)

        return _response_to_result(response)

    def invoke(self, input, config=None, **kwargs):
        return normalize_content(super().invoke(input, config, **kwargs))

    async def ainvoke(self, input, config=None, **kwargs):
        res = await super().ainvoke(input, config, **kwargs)
        return normalize_content(res)


class GoogleClient(BaseLLMClient):
    """Client for Google Gemini models."""

    def __init__(self, model: str, base_url: str | None = None, **kwargs):
        super().__init__(model, base_url, **kwargs)

    def get_llm(self) -> Any:
        """Return configured ChatGoogleGenerativeAI instance."""
        self.warn_if_unknown_model()
        llm_kwargs = {"model": self.model}

        if self.base_url:
            llm_kwargs["base_url"] = self.base_url

        for key in ("timeout", "max_retries", "temperature", "max_output_tokens",
                    "callbacks", "http_client", "http_async_client"):
            if key in self.kwargs:
                llm_kwargs[key] = self.kwargs[key]

        # Unified api_key maps to provider-specific google_api_key
        google_api_key = self.kwargs.get("api_key") or self.kwargs.get("google_api_key")
        if google_api_key:
            llm_kwargs["google_api_key"] = google_api_key

        # Gemini 3.x takes the string ``thinking_level`` (the integer
        # ``thinking_budget`` was for the now-retired 2.5 line). Pro accepts
        # low/high; Flash also accepts minimal/medium — so map an unsupported
        # "minimal" on Pro to the nearest level it does accept.
        thinking_level = self.kwargs.get("thinking_level")
        if thinking_level:
            if "pro" in self.model.lower() and thinking_level == "minimal":
                thinking_level = "low"
            llm_kwargs["thinking_level"] = thinking_level

        return NormalizedChatGoogleGenerativeAI(**llm_kwargs)

    def validate_model(self) -> bool:
        """Validate model for Google."""
        return validate_model("google", self.model)
