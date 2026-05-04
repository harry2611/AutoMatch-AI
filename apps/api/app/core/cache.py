from __future__ import annotations

import json
import logging
from typing import Any

import redis

from app.core.config import settings

logger = logging.getLogger(__name__)

# Module-level singleton — intentionally not cached with lru_cache so that
# a Redis container that starts after the API process can be picked up on the
# next call rather than staying permanently None for the process lifetime.
_redis_client: redis.Redis | None = None


def get_redis_client() -> redis.Redis | None:
    """Return a live Redis client, or None if Redis is unavailable.

    The client is created once and reused.  If the connection is found to be
    dead on a subsequent call, it is re-established so that transient
    container-startup races don't permanently disable caching.
    """
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except redis.RedisError:
            logger.warning("Redis connection lost — attempting to reconnect.")
            _redis_client = None

    try:
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True, socket_connect_timeout=2)
        client.ping()
        _redis_client = client
        return _redis_client
    except redis.RedisError as exc:
        logger.warning("Redis unavailable (%s) — caching disabled for this request.", exc)
        return None


def cache_json(key: str, payload: Any, ttl_seconds: int = 300) -> None:
    client = get_redis_client()
    if client is None:
        return
    try:
        client.setex(key, ttl_seconds, json.dumps(payload, default=str))
    except redis.RedisError as exc:
        logger.warning("cache_json failed for key=%s: %s", key, exc)


def read_json(key: str) -> Any | None:
    client = get_redis_client()
    if client is None:
        return None
    try:
        raw = client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except (redis.RedisError, json.JSONDecodeError) as exc:
        logger.warning("read_json failed for key=%s: %s", key, exc)
        return None
