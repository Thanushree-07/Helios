from fastapi import APIRouter, Depends

from app.middleware.auth import require_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

service = ChatService()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, api_key: str = Depends(require_api_key)):

    return service.process_chat(request, client_id=api_key)