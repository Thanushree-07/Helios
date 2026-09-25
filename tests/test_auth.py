def test_chat_without_api_key_returns_401(client):
    response = client.post("/chat", json={"prompt": "hi"})
    assert response.status_code == 401


def test_chat_with_wrong_api_key_returns_401(client):
    response = client.post(
        "/chat",
        json={"prompt": "hi"},
        headers={"X-API-Key": "wrong-key"},
    )
    assert response.status_code == 401


def test_health_does_not_require_api_key(client):
    response = client.get("/health")
    assert response.status_code == 200