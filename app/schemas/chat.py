from pydantic import BaseModel

class ChatRequest(BaseModel):
    model:str
    prompt:str

class ChatResponse(BaseModel):
    response:str