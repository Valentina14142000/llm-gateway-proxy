import pytest
from fastapi.testclient import TestClient
import respx
from httpx import Response
from src.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "llm-gateway-proxy"}

@respx.mock
def test_chat_completion_proxy():
    # Mock the upstream OpenAI endpoint
    respx.post("https://api.openai.com/v1/chat/completions").mock(
        return_value=Response(200, json={"choices": [{"text": "Hello world!"}]})
    )

    response = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk-testtoken"},
        json={"model": "gpt-4", "messages": [{"role": "user", "content": "Hi"}]}
    )

    assert response.status_code == 200
    assert response.json() == {"choices": [{"text": "Hello world!"}]}
