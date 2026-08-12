from app.schemas.chat import ChatRequest,ChatResponse
from app.services.provider_selector import ProviderSelector
from app.providers.provider_factory import ProviderFactory
class ChatService:
    def __init__(self):
        self.selector=ProviderSelector()

    def process_chat(self, request: ChatRequest) -> ChatResponse:

        provider_name = self.selector.select_provider(request.prompt)

        provider = ProviderFactory.get_provider(provider_name)

        answer = provider.generate(request.prompt)

        return ChatResponse(
            response=answer
        )
   
   
   