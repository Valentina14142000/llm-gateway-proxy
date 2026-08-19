import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

# Simple Redis connection pool for rate limiting
redis_client = redis.Redis.from_url("redis://localhost:6379/0", decode_responses=True)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.rpm = requests_per_minute

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks
        if request.url.path == "/health":
            return await call_next(request)

        # Extract tenant API key from headers
        api_key = request.headers.get("Authorization", "anonymous")
        window_key = f"rate_limit:{api_key}:{int(time.time() // 60)}"

        try:
            # Atomic increment with TTL
            pipe = redis_client.pipeline()
            pipe.incr(window_key)
            pipe.expire(window_key, 60)
            current_requests, _ = await pipe.execute()

            if current_requests > self.rpm:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Rate limit exceeded. Too many requests per minute."
                )
        except redis.RedisError:
            # Fail open if Redis is down to preserve availability
            pass

        response = await call_next(request)
        return response
