from fastapi import Header,HTTPException,status
from app.core.config import settings

def require_api_key(x_api_key:str|None=Header(default=None))->None:
    if x_api_key is None or x_api_key!=settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key"
        )