from fastapi import APIRouter
from app.schemas.health import HealthResponse
router=APIRouter()

@router.get("/health",response_model=HealthResponse)
def health():
    return{
    "status":"Healthy"
}