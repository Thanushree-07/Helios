import hashlib
import logging
import time

from app.providers.provider_factory import ProviderFactory
from app.redis_client import redis_client
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.provider_selector import ProviderSelector
from app.services.rate_limiter import RateLimiter

logger = logging.getLogger("helios.chat")

CACHE_TTL_SECONDS = 300


def _cache_key(prompt: str) -> str:
   
    digest = hashlib.sha256(prompt.strip().lower().encode("utf-8")).hexdigest()
    return f"chat:{digest}"


class ChatService:

    def __init__(self):
        self.selector = ProviderSelector()
        self.rate_limiter = RateLimiter()

    def process_chat(self, request: ChatRequest) -> ChatResponse:

        # Stage 2: rate limit
        self.rate_limiter.check("user1")

        start_time = time.perf_counter()
        cache_key = _cache_key(request.prompt)

        # Stage 3: cache check — BEFORE routing, so a hit never pays for
        # the router's classification call either.
        cached_answer = redis_client.get(cache_key)

        if cached_answer is not None:
            elapsed = time.perf_counter() - start_time
            logger.info("cache hit (%.4fs)", elapsed)
            return ChatResponse(response=cached_answer)

        logger.info("cache miss — routing and calling provider")

        # Stage 4: router picks a provider (cost of this call is now only
        # paid on a genuine cache miss)
        provider_name = self.selector.select_provider(request.prompt)
        provider = ProviderFactory.get_provider(provider_name)

        # Stage 6: call the LLM
        answer = provider.generate(request.prompt)

        # Stage 7: save to cache
        redis_client.set(cache_key, answer, ex=CACHE_TTL_SECONDS)

        elapsed = time.perf_counter() - start_time
        logger.info("provider=%s elapsed=%.4fs", provider_name, elapsed)

        return ChatResponse(response=answer)