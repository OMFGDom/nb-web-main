from fastapi import Depends
from src.db.redis import get_redis
from redis.asyncio import Redis

async def put_object_to_cache(key, context, expire,  redis: Redis = Depends(get_redis)):
    print('Set Object To Cache')
    await redis.set(
        key,
        context.json(),
        expire
    )