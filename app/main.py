from fastapi import FastAPI
from app.core.config import settings
from app.api.health import router as health_router 
from app.api.chat import router as chat_router
app=FastAPI(
    title=settings.APP_NAME,
    description="Distributed LLM Gateway",
    version=settings.VERSION
)
app.include_router(health_router)
app.include_router(chat_router)
@app.get("/")
def root():
    return{
        "Project":settings.APP_NAME,
        "Status":"Running"
    }

