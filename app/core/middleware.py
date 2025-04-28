from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import time
from app.core.config import settings
import redis
import json
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class InMemoryRateLimiter:
    def __init__(self, window: int):
        self.window = window
        self.requests = defaultdict(list)
    
    def add_request(self, client_ip: str) -> int:
        current = time.time()
        self.requests[client_ip] = [ts for ts in self.requests[client_ip] if current - ts < self.window]
        self.requests[client_ip].append(current)
        return len(self.requests[client_ip])

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.rate_limit = settings.RATE_LIMIT_REQUESTS
        self.window = settings.RATE_LIMIT_WINDOW
        
        # Try to initialize Redis client
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Using Redis for rate limiting")
        except (redis.ConnectionError, redis.exceptions.ConnectionError):
            self.use_redis = False
            self.in_memory_limiter = InMemoryRateLimiter(self.window)
            logger.warning("Redis not available, using in-memory rate limiting")

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for OPTIONS requests (CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host
        
        if self.use_redis:
            try:
                # Create a key for the IP
                key = f"rate_limit:{client_ip}"
                current = time.time()
                
                # Create a pipeline for atomic operations
                pipe = self.redis_client.pipeline()
                
                # Add current request timestamp to sorted set
                pipe.zadd(key, {str(current): current})
                
                # Remove timestamps outside the window
                pipe.zremrangebyscore(key, 0, current - self.window)
                
                # Count requests in current window
                pipe.zcard(key)
                
                # Set key expiration
                pipe.expire(key, self.window)
                
                # Execute pipeline
                _, _, request_count, _ = pipe.execute()
            except redis.exceptions.RedisError as e:
                logger.error(f"Redis error: {e}")
                # Fallback to in-memory on Redis error
                self.use_redis = False
                self.in_memory_limiter = InMemoryRateLimiter(self.window)
                request_count = self.in_memory_limiter.add_request(client_ip)
        else:
            request_count = self.in_memory_limiter.add_request(client_ip)
        
        # Check if request count exceeds limit
        if request_count > self.rate_limit:
            raise HTTPException(
                status_code=429,
                detail="Too many requests"
            )
        
        # Process the request
        response = await call_next(request)
        return response 