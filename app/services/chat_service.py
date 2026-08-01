from app.schemas.chat import ChatRequest,ChatResponse
from app.providers.llama_provider import LlamaProvider
from app.providers.groq_provider import GroqProvider
class ChatService:
    def __init__(self):
        self.groq_provider=GroqProvider()

    def process_chat(self,request:ChatRequest)->ChatResponse:
        answer=self.groq_provider.generate(
            request.prompt
        )
        

        return ChatResponse(
            response=answer
        )
