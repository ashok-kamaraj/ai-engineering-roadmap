from unittest.mock import patch

from fastapi.testclient import TestClient

from app.api import app
from app.llm_client import LLMError

client = TestClient(app)


def test_health_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chat_returns_response_on_success():
    with patch("app.api.send_message", return_value="4") as mock_send:
        response = client.post("/chat", json={"message": "What is 2+2?"})

    assert response.status_code == 200
    assert response.json() == {"response": "4"}
    mock_send.assert_called_once()


def test_chat_rejects_blank_message():
    response = client.post("/chat", json={"message": "   "})

    assert response.status_code == 422


def test_chat_returns_502_on_llm_error():
    with patch("app.api.send_message", side_effect=LLMError("Rate limit exceeded.")):
        response = client.post("/chat", json={"message": "Hi"})

    assert response.status_code == 502
    assert response.json() == {"detail": "Rate limit exceeded."}
