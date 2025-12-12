import json
from redis_client import redis_client


async def cache_get(key: str):
    data = await redis_client.get(key)
    if not data:
        return None

    try:
        return json.loads(data)
    except Exception:
        
        return None


async def cache_set(key: str, value, expire_seconds: int = 300):
    """
    Serializes any Python object (including datetime) and stores in Redis.
    """
    serialized = json.dumps(value, default=str)   # ⭐ FIX: handles datetime

    await redis_client.set(
        key,
        serialized,
        ex=expire_seconds   # auto-expire
    )


async def cache_delete(key: str):
    await redis_client.delete(key)
