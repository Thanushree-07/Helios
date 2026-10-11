import hashlib
import logging
import time

from fastapi import HTTPException
from app.cache.semantic import semantic_cache
from app.providers.provider_factory import ProviderFactory
from app.redis_client import redis_client
from app.resilience.circuit_breaker import CircuitBreakerRegistry
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.provider_selector import ProviderSelector
from app.services.rate_limiter import RateLimiter
from app.observability.metrics import PROVIDER_FAILURES, REQUEST_COUNT, REQUEST_LATENCY

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
                PROVIDER_FAILURES.labels(provider=provider_name).inc()

                logger.warning("provider %s failed (%s), trying next", provider_name, e)
                last_error = e
                continue

        raise HTTPException(
            status_code=503,
            detail="All providers are currently unavailable.",
        ) from last_error
    def process_chat(self, request: ChatRequest, client_id: str) -> ChatResponse:
        # Used by the normal /chat endpoint. Same behaviour as before.
        return ChatResponse(response=self.run(request, client_id)["response"])

    def run(self, request: ChatRequest, client_id: str) -> dict:
        """
        Does the whole pipeline and returns what really happened:
        the answer, which provider answered, cache hit or not, and the
        stage-by-stage trace that the Playground shows.
        """
        # Stage 2: rate limit (raises an error if the client is over the limit)
        self.rate_limiter.check(client_id)

        start_time = time.perf_counter()
        cache_key = _cache_key(request.prompt)

        # Stage 3a: exact cache
        cached_answer = redis_client.get(cache_key)
        if cached_answer is not None:
            elapsed = time.perf_counter() - start_time
            REQUEST_COUNT.labels(cache_result="hit_exact", provider="none").inc()
            REQUEST_LATENCY.labels(cache_result="hit_exact").observe(elapsed)
            logger.info("cache hit (exact) (%.4fs)", elapsed)
            return {
                "response": cached_answer,
                "provider": "cache",
                "cache": "exact",
                "failover": [],
                "trace": [
                    {"stage": "cache", "result": "hit", "detail": "Exact match found in Redis"},
                    {"stage": "router", "result": "skip", "detail": "Skipped (cache hit)"},
                    {"stage": "breaker", "result": "skip", "detail": "Skipped (cache hit)"},
                    {"stage": "llm", "result": "skip", "detail": "No LLM call needed"},
                    {"stage": "save", "result": "skip", "detail": "Already cached"},
                ],
            }

        # Stage 3b: semantic cache
        similar_key, similarity_score = semantic_cache.find_similar(request.prompt)
        semantic_answer = None
        if similar_key is not None:
            # The index is in memory but answers expire in Redis after 5 min.
            # If the answer is gone, treat it as a miss instead of crashing.
            semantic_answer = redis_client.get(similar_key)
        logger.info("semantic best match score=%.3f (threshold=0.75)", similarity_score)

        if semantic_answer is not None:
            elapsed = time.perf_counter() - start_time
            REQUEST_COUNT.labels(cache_result="hit_semantic", provider="none").inc()
            REQUEST_LATENCY.labels(cache_result="hit_semantic").observe(elapsed)
            logger.info("cache hit (semantic, score=%.3f) (%.4fs)", similarity_score, elapsed)
            return {
                "response": semantic_answer,
                "provider": "cache",
                "cache": "semantic",
                "failover": [],
                "trace": [
                    {"stage": "cache", "result": "hit", "detail": f"Semantic match (similarity {similarity_score:.2f})"},
                    {"stage": "router", "result": "skip", "detail": "Skipped (cache hit)"},
                    {"stage": "breaker", "result": "skip", "detail": "Skipped (cache hit)"},
                    {"stage": "llm", "result": "skip", "detail": "No LLM call needed"},
                    {"stage": "save", "result": "skip", "detail": "Already cached"},
                ],
            }

        logger.info("cache miss — routing and calling provider")

        # Stage 4: router picks a provider
        provider_name = self.selector.select_provider(request.prompt)

        # Stage 5 + 6: circuit breaker + LLM call, with failover
        answer, used_provider = self._call_with_failover(provider_name, request.prompt)
        failover = [] if used_provider == provider_name else [provider_name]

        # Stage 7: save to both caches
        redis_client.set(cache_key, answer, ex=CACHE_TTL_SECONDS)
        semantic_cache.add(request.prompt, cache_key)

        elapsed = time.perf_counter() - start_time
        logger.info("provider=%s elapsed=%.4fs", used_provider, elapsed)
        REQUEST_COUNT.labels(cache_result="miss", provider=used_provider).inc()
        REQUEST_LATENCY.labels(cache_result="miss").observe(elapsed)

        if failover:
            breaker_detail = f"{provider_name} unavailable, failed over to {used_provider}"
        else:
            breaker_detail = f"{used_provider} circuit closed"

        return {
            "response": answer,
            "provider": used_provider,
            "cache": None,
            "failover": failover,
            "trace": [
                {"stage": "cache", "result": "pass", "detail": "Miss in exact and semantic cache"},
                {"stage": "router", "result": "pass", "detail": f"Router picked {provider_name}"},
                {"stage": "breaker", "result": "pass", "detail": breaker_detail},
                {"stage": "llm", "result": "pass", "detail": f"{used_provider} answered"},
                {"stage": "save", "result": "pass", "detail": f"Saved to Redis (TTL {CACHE_TTL_SECONDS}s) and semantic index"},
            ],
        }
        