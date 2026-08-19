from app.schemas.chat import ChatRequest, ChatResponse
from app.services.provider_selector import ProviderSelector
from app.providers.provider_factory import ProviderFactory


class ChatService:

    def __init__(self):
        self.selector = ProviderSelector()

    def process_chat(self, request: ChatRequest) -> ChatResponse:

        decision = self.selector.select_provider(request.prompt)

        provider = ProviderFactory.get_provider(decision.provider)

        answer = provider.generate(request.prompt)

        return ChatResponse(
            response=answer
        )