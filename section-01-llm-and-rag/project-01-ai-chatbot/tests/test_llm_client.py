from types import SimpleNamespace
from unittest.mock import patch

import anthropic
import httpx2
import pytest

from app.llm_client import LLMError, send_message

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def _text_response(text: str) -> SimpleNamespace:
    return SimpleNamespace(
        content=[SimpleNamespace(type="text", text=text)],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5),
    )


def test_send_message_returns_text_on_success():
    with patch("app.llm_client._client.messages.create", return_value=_text_response("Hello!")) as mock_create:
        result = send_message([{"role": "user", "content": "Hi"}])

    assert result == "Hello!"
    mock_create.assert_called_once()


def test_send_message_forwards_full_conversation_history():
    history = [
        {"role": "user", "content": "What is 5 + 7?"},
        {"role": "assistant", "content": "12"},
        {"role": "user", "content": "Multiply that by 2"},
    ]
    with patch("app.llm_client._client.messages.create", return_value=_text_response("24")) as mock_create:
        send_message(history)

    assert mock_create.call_args.kwargs["messages"] == history


def test_send_message_raises_llm_error_on_authentication_failure():
    response = httpx2.Response(401, request=REQUEST)
    error = anthropic.AuthenticationError("invalid key", response=response, body=None)

    with patch("app.llm_client._client.messages.create", side_effect=error):
        with pytest.raises(LLMError, match="Authentication failed"):
            send_message([{"role": "user", "content": "Hi"}])


def test_send_message_raises_llm_error_on_rate_limit():
    response = httpx2.Response(429, request=REQUEST)
    error = anthropic.RateLimitError("too many requests", response=response, body=None)

    with patch("app.llm_client._client.messages.create", side_effect=error):
        with pytest.raises(LLMError, match="Rate limit"):
            send_message([{"role": "user", "content": "Hi"}])


def test_send_message_raises_llm_error_on_connection_failure():
    error = anthropic.APIConnectionError(request=REQUEST)

    with patch("app.llm_client._client.messages.create", side_effect=error):
        with pytest.raises(LLMError, match="Could not reach"):
            send_message([{"role": "user", "content": "Hi"}])


def test_send_message_raises_llm_error_on_server_error():
    response = httpx2.Response(500, request=REQUEST)
    error = anthropic.InternalServerError("server exploded", response=response, body=None)

    with patch("app.llm_client._client.messages.create", side_effect=error):
        with pytest.raises(LLMError, match="status 500"):
            send_message([{"role": "user", "content": "Hi"}])
