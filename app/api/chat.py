from fastapi import APIRouter

from app.schemas.chat import ChatRequest

router = APIRouter()


@router.post("/chat", response_model=ChatRequest)
def chat(request: ChatRequest):

    return {
        "prompt":request.prompt
    }