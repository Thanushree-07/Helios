from fastapi import Header, HTTPException, status

from app.core.config import settings


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """
    FastAPI dependency that enforces Stage 1 of the pipeline: AUTH.

    Returns the validated API key itself, so callers further down the
    pipeline (like rate limiting) can identify WHICH client is calling,
    instead of treating every request as the same anonymous user.
    """
    if x_api_key is None or x_api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid API key. Set the X-API-Key header.",
        )
    return x_api_key