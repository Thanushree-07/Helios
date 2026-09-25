def test_chat_with_correct_key_returns_answer(client, monkeypatch):
    # Fake rate limiter's Redis calls
    monkeypatch.setattr(
        "app.services.rate_limiter.redis_client.incr",
        lambda key: 1,
    )
    monkeypatch.setattr(
        "app.services.rate_limiter.redis_client.expire",
        lambda key, seconds: None,
    )

    # Fake Redis: always a cache miss
    monkeypatch.setattr(
        "app.services.chat_service.redis_client.get",
        lambda key: None,
    )
    monkeypatch.setattr(
        "app.services.chat_service.redis_client.set",
        lambda key, value, ex=None: None,
    )

    # Fake router: always says "general, low"
    from app.schemas.routing import RoutingDecision
    monkeypatch.setattr(
        "app.services.provider_selector.RouterService.analyze",
        lambda self, prompt: RoutingDecision(task_type="general", complexity="low"),
    )

    # Fake provider: returns a fixed answer instead of calling a real AI
    class FakeProvider:
        def generate(self, prompt):
            return "this is a fake answer"

    monkeypatch.setattr(
        "app.services.chat_service.ProviderFactory.get_provider",
        lambda name: FakeProvider(),
    )

    response = client.post(
        "/chat",
        json={"prompt": "hello"},
        headers={"X-API-Key": "test-key-123"},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "this is a fake answer"}


def test_chat_returns_cached_answer_on_hit(client, monkeypatch):
    # Fake rate limiter's Redis calls
    monkeypatch.setattr(
        "app.services.rate_limiter.redis_client.incr",
        lambda key: 1,
    )
    monkeypatch.setattr(
        "app.services.rate_limiter.redis_client.expire",
        lambda key, seconds: None,
    )

    monkeypatch.setattr(
        "app.services.chat_service.redis_client.get",
        lambda key: "cached answer from before",
    )

    response = client.post(
        "/chat",
        json={"prompt": "hello again"},
        headers={"X-API-Key": "test-key-123"},
    )

    assert response.status_code == 200
    assert response.json() == {"response": "cached answer from before"}