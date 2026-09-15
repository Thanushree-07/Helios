import hashlib
import logging
import time

from fastapi import HTTPException

from app.providers.provider_factory import ProviderFactory
from app.redis_client import redis_client
from app.resilience.circuit_breaker import CircuitBreakerRegistry
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.provider_selector import ProviderSelector
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger("helios.chat")

CACHE_TTL_SECONDS = 300

# Order to try providers in if the chosen one is down/unhealthy.
# Ollama sits last until it's installed and wired into provider_selector.
FALLBACK_ORDER = ["groq", "gemini", "ollama"]


def _cache_key(prompt: str) -> str:
    digest = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
    return f"chat:{digest}"


class ChatService:

    def __init__(self):
        self.selector = ProviderSelector()
        self.rate_limiter = RateLimiter()

    def _call_with_failover(self, primary_provider: str, prompt: str) -> tuple[str, str]:
        """
        Try the router's chosen provider first. If its circuit is open, or
        the call itself fails (like Gemini's 503 you just hit), fall
        through to the next provider instead of failing the whole request.
        """
        candidates = [primary_provider] + [p for p in FALLBACK_ORDER if p != primary_provider]

        last_error: Exception | None = None

        for provider_name in candidates:
            breaker = CircuitBreakerRegistry.get(provider_name)

            if not breaker.allow_request():
                logger.info("circuit OPEN for %s, skipping", provider_name)
                continue

            try:
                provider = ProviderFactory.get_provider(provider_name)
                answer = provider.generate(prompt)
                breaker.record_success()
                return answer, provider_name

            except Exception as e:
                breaker.record_failure()
                logger.warning("provider %s failed (%s), trying next", provider_name, e)
                last_error = e
                continue

        raise HTTPException(
            status_code=503,
            detail="All providers are currently unavailable.",
        ) from last_error

    def process_chat(self, request: ChatRequest) -> ChatResponse:

        # Stage 2: rate limit
        self.rate_limiter.check("user1")

        start_time = time.perf_counter()
        cache_key = _cache_key(request.prompt)

        # Stage 3: cache check — before routing
        cached_answer = redis_client.get(cache_key)

        if cached_answer is not None:
            elapsed = time.perf_counter() - start_time
            logger.info("cache hit (%.4fs)", elapsed)
            return ChatResponse(response=cached_answer)

        logger.info("cache miss — routing and calling provider")

        # Stage 4: router picks a provider
        provider_name = self.selector.select_provider(request.prompt)

        # Stage 5 + 6: circuit breaker check + call LLM, with failover
        answer, used_provider = self._call_with_failover(provider_name, request.prompt)

        # Stage 7: save to cache
        redis_client.set(cache_key, answer, ex=CACHE_TTL_SECONDS)

        elapsed = time.perf_counter() - start_time
        logger.info("provider=%s elapsed=%.4fs", used_provider, elapsed)

        return ChatResponse(response=answer)