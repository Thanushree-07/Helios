from fastapi import APIRouter,Depends

from app.schemas.chat import ChatRequest,ChatResponse
from app.services.chat_service import ChatService
from app.middleware.auth import require_api_key

router = APIRouter()

service=ChatService()
@router.post("/chat", response_model=ChatResponse,dependencies=[Depends(require_api_key)])
def chat(request: ChatRequest):

    return(service.process_chat(request))