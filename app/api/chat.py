from fastapi import APIRouter

from app.schemas.chat import ChatRequest,ChatResponse

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):

    if request.model=="llama3":
        answer=f"[Llama3] You asked:{request.propmt}"
    elif request.model=="gemini":
        answer=f"[gemini] You asked:{request.prompt}"
    else:
        answer="Model not supported"
    return{
        "response":answer
    }