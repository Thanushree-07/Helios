from app.redis_client import redis_client
from fastapi import HTTPException


class RateLimiter:

    def __init__(self, limit: int = 10, window: int = 60):
        self.limit = limit
        self.window = window

    def check(self, client_id: str):

        key = f"rate_limit:{client_id}"

        request_count = redis_client.incr(key)

        if request_count == 1:
            redis_client.expire(key, self.window)

        print("RATE LIMIT COUNT:", request_count)

        if request_count > self.limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later."
            )