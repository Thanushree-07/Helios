import logging
from fastapi import FastAPI, Response
from app.core.config import settings
from app.api.health import router as health_router 
from app.api.chat import router as chat_router
from prometheus_client import CONTENT_TYPE_LATEST,generate_latest
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.db import models  # noqa: F401
from app.api.gateway import router as gateway_router
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)
app=FastAPI(
    title=settings.app_name,
    description="Distributed LLM Gateway",
    version=settings.version
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Base.metadata.create_all(bind=engine)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(gateway_router)
@app.get("/")
def root():
    return{
        "Project":settings.app_name,
        "Status":"Running"
    }

@app.get("/metrics")
def metrics():
    return Response(content=generate_latest(),media_type=CONTENT_TYPE_LATEST)
