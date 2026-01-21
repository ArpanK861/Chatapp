import os
import redis.asyncio as redis

redis_pool = redis.ConnectionPool.from_url(
    os.getenv("REDIS_URL", "redis://localhost:6379/0"), 
    decode_responses=True
)

def get_redis_client():
    return redis.Redis(connection_pool=redis_pool)

async def set_online(user):
    r = get_redis_client()
    await r.sadd("online_users", user.username)

async def set_offline(user):
    r = get_redis_client()
    await r.srem("online_users", user.username)

async def typing_start(room, user):
    r = get_redis_client()
    await r.set(f"typing:{room}:{user.username}", "1", ex=5)

async def typing_end(room, user):
    r = get_redis_client()
    await r.delete(f"typing:{room}:{user.username}")

async def get_online_count():
    r = get_redis_client()
    return await r.scard("online_users")