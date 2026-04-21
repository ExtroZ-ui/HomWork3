import json
from typing import Any

from redis import Redis
from redis.exceptions import RedisError

REDIS_URL = "redis://localhost:6379/0"

redis_client = Redis.from_url(REDIS_URL, decode_responses=True)


def build_cache_key(prefix: str, identifier: str) -> str:
    return f"cache:{prefix}:{identifier}"


def get_cache(key: str) -> Any | None:
    try:
        value = redis_client.get(key)
        if value is None:
            return None
        return json.loads(value)
    except (RedisError, json.JSONDecodeError):
        return None


def set_cache(key: str, value: Any, ttl: int = 300) -> None:
    try:
        redis_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
    except (RedisError, TypeError):
        pass


def clear_cache(prefix: str = "cache:") -> None:
    try:
        keys = redis_client.keys(f"{prefix}*")
        if keys:
            redis_client.delete(*keys)
    except RedisError:
        pass