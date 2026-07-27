from fastapi import FastAPI
from app.core.config import settings
from app.api.health import router as health_router 
app=FastAPI(
    title=settings.APP_NAME,
    description="Distributed LLM Gateway",
    version=settings.VERSION
)
app.include_router(health_router)
@app.get("/")
def root():
    return{
        "Project":settings.APP_NAME,
        "Status":"Running"
    }

