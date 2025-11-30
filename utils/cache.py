import json
from redis_client import redis_client

async def cache_get(key: str):
    data = await redis_client.get(key)
    if data:
        return json.loads(data)
    return None


async def cache_set(key: str, value, expire_seconds: int = 300):
    await redis_client.set(
        key,
        json.dumps(value),
        ex=expire_seconds   # auto-delete
    )


async def cache_delete(key: str):
    await redis_client.delete(key)
