import asyncio
import warnings
from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage

from fixedincomeagent.llm_clients.google_client import GoogleClient


@pytest.mark.unit
def test_google_client_routes_via_chats_create_and_send_message():
    client = GoogleClient(model="gemini-3.1-flash-lite", api_key="mock-key")
    llm = client.get_llm()

    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = []
    mock_response.usage_metadata = None
    mock_response.automatic_function_calling_history = []
    mock_chat.send_message.return_value = mock_response

    mock_sdk_client = MagicMock()
    mock_sdk_client.chats.create.return_value = mock_chat
    llm.client = mock_sdk_client

    result = llm.invoke([HumanMessage(content="Hello Gemini")])

    mock_sdk_client.models.generate_content.assert_not_called()
    mock_sdk_client.chats.create.assert_called_once()
    create_kwargs = mock_sdk_client.chats.create.call_args[1]
    assert create_kwargs["model"] == "gemini-3.1-flash-lite"
    assert create_kwargs["history"] is None

    mock_chat.send_message.assert_called_once()
    send_arg = mock_chat.send_message.call_args[0][0]
    assert len(send_arg) == 1
    assert send_arg[0].text == "Hello Gemini"
    assert result.content == ""


@pytest.mark.unit
def test_google_client_multi_turn_history():
    client = GoogleClient(model="gemini-3.1-flash-lite", api_key="mock-key")
    llm = client.get_llm()

    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = []
    mock_response.usage_metadata = None
    mock_response.automatic_function_calling_history = []
    mock_chat.send_message.return_value = mock_response

    mock_sdk_client = MagicMock()
    mock_sdk_client.chats.create.return_value = mock_chat
    llm.client = mock_sdk_client

    messages = [
        HumanMessage(content="First message"),
        AIMessage(content="First response"),
        HumanMessage(content="Second message"),
    ]
    llm.invoke(messages)

    mock_sdk_client.models.generate_content.assert_not_called()
    mock_sdk_client.chats.create.assert_called_once()
    create_kwargs = mock_sdk_client.chats.create.call_args[1]
    history = create_kwargs["history"]
    assert len(history) == 2
    assert history[0].parts[0].text == "First message"
    assert history[1].parts[0].text == "First response"

    mock_chat.send_message.assert_called_once()
    send_arg = mock_chat.send_message.call_args[0][0]
    assert len(send_arg) == 1
    assert send_arg[0].text == "Second message"


@pytest.mark.unit
def test_google_client_agenerate_routes_via_chats_create():
    async def _run():
        client = GoogleClient(model="gemini-3.1-flash-lite", api_key="mock-key")
        llm = client.get_llm()

        mock_chat = MagicMock()
        mock_response = MagicMock()
        mock_response.candidates = []
        mock_response.usage_metadata = None
        mock_response.automatic_function_calling_history = []
        mock_chat.send_message = AsyncMock(return_value=mock_response)

        mock_async_client = MagicMock()
        mock_async_client.chats.create.return_value = mock_chat
        mock_sdk_client = MagicMock()
        mock_sdk_client.aio = mock_async_client
        llm.client = mock_sdk_client

        result = await llm.ainvoke([HumanMessage(content="Hello Async")])

        mock_async_client.models.generate_content.assert_not_called()
        mock_async_client.chats.create.assert_called_once()
        create_kwargs = mock_async_client.chats.create.call_args[1]
        assert create_kwargs["model"] == "gemini-3.1-flash-lite"
        assert create_kwargs["history"] is None

        mock_chat.send_message.assert_awaited_once()
        send_arg = mock_chat.send_message.call_args[0][0]
        assert len(send_arg) == 1
        assert send_arg[0].text == "Hello Async"
        assert result.content == ""

    asyncio.run(_run())


@pytest.mark.unit
def test_google_client_tool_call_no_afc_warning():
    client = GoogleClient(model="gemini-3.1-flash-lite", api_key="mock-key")
    llm = client.get_llm()

    mock_chat = MagicMock()
    mock_response = MagicMock()
    mock_response.candidates = []
    mock_response.usage_metadata = None
    mock_response.automatic_function_calling_history = []
    mock_chat.send_message.return_value = mock_response

    mock_sdk_client = MagicMock()
    mock_sdk_client.chats.create.return_value = mock_chat
    llm.client = mock_sdk_client

    def sample_tool(query: str) -> str:
        """Sample tool docstring."""
        return query

    tool_llm = llm.bind_tools([sample_tool])

    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        tool_llm.invoke([HumanMessage(content="Use tool")])

    mock_sdk_client.models.generate_content.assert_not_called()
    mock_sdk_client.chats.create.assert_called_once()
    mock_chat.send_message.assert_called_once()

    afc_warnings = [
        w
        for w in recorded_warnings
        if "AFC" in str(w.message) or "automatic function calling" in str(w.message).lower()
    ]
    assert len(afc_warnings) == 0

