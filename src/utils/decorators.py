from fastapi import Request, Depends
from fastapi.responses import Response
from functools import wraps
from redis.asyncio import Redis
from src.db.database import get_db
from src.db.redis import get_redis
from redis.exceptions import RedisError

def cache_response(redis_key_prefix: str, expiration: int):
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            redis: Redis = await get_redis()
            cache_key_parts = [
                redis_key_prefix,
                kwargs.get('slug', ''),
                str(kwargs.get('page', '')),
                kwargs.get('type', ''),
                kwargs.get('q', ''),
                str(kwargs.get('year', '')),
            ]

            cache_key = "_".join(filter(None, cache_key_parts))
            print(cache_key)
            cached_response = await redis.get(cache_key)
            if cached_response:
                print("from cache")
                return Response(cached_response)
            print("not from cache")
            response = await func(request, *args, **kwargs)
            #await redis.set(cache_key, response.body, ex=expiration)
            try:
                await redis.set(cache_key, response.body, ex=expiration)
            except RedisError as e:
                print(f"Redis write failed: {e}")
            return response

        return wrapper

    return decorator
