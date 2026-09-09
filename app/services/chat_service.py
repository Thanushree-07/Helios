from app.schemas.chat import ChatRequest, ChatResponse
from app.services.provider_selector import ProviderSelector
from app.providers.provider_factory import ProviderFactory
from app.redis_client import redis_client
import time 


class ChatService:

    def __init__(self):
        self.selector = ProviderSelector()

    def process_chat(self, request: ChatRequest) -> ChatResponse:
        start_time=time.perf_counter()

        print("PROMPT RECEIVED:", repr(request.prompt))

        cached_answer = redis_client.get(request.prompt)

        print("REDIS RETURNED:", repr(cached_answer))

        if cached_answer is not None:
            elapsed=time.perf_counter()-start_time
            print(f"🔥 CACHE HIT - Response came from Redis and time elapsed:{elapsed:.4f}seconds")

            return ChatResponse(
                response=cached_answer
            )

        print("❌ CACHE MISS - Calling provider")

        provider_name = self.selector.select_provider(request.prompt)
        provider = ProviderFactory.get_provider(provider_name)

        answer = provider.generate(request.prompt)

        redis_client.set(request.prompt, answer, ex=300)

        elapsed = time.perf_counter() - start_time

        print("💾 STORED RESPONSE IN REDIS and elapsed time =",elapsed)

        return ChatResponse(
            response=answer
        )