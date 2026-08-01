from fastapi import APIRouter

from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()

service=ChatService()
@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    return(service.process_chat(request))