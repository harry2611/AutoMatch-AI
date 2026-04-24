from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

import redis

from app.core.config import settings


@lru_cache(maxsize=1)
def get_redis_client() -> redis.Redis | None:
    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return client
    except redis.RedisError:
        return None


def cache_json(key: str, payload: Any, ttl_seconds: int = 300) -> None:
    client = get_redis_client()
    if client is None:
        return
    client.setex(key, ttl_seconds, json.dumps(payload, default=str))


def read_json(key: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    raw = client.get(key)
    if raw is None:
        return None
    return json.loads(raw)

