from .presence import get_redis_client

async def is_rate_limited(username):
    r = get_redis_client()
    key = f"rate_limit:{username}"
    try:
        count = await r.incr(key)
        if count == 1:
            await r.expire(key, 3)  
        return count > 5
    finally:
        await r.close()