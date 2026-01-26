"""Redis Cache Management Service"""

import json
import redis
from typing import Any, Optional, Union
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder


class CacheManager:
    """Redis cache manager with cache-aside pattern"""
    
    def __init__(self, redis_url: Optional[str] = None, default_ttl: int = 3600):
        self.redis_url = redis_url or getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0')
        self.default_ttl = default_ttl
        self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with cache-aside pattern"""
        try:
            cached_value = self.redis_client.get(key)
            if cached_value is not None:
                return json.loads(cached_value)
            return default
        except (redis.RedisError, json.JSONDecodeError):
            return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with TTL"""
        try:
            ttl = ttl or self.default_ttl
            serialized_value = json.dumps(value, cls=DjangoJSONEncoder)
            return self.redis_client.setex(key, ttl, serialized_value)
        except (redis.RedisError, TypeError):
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        try:
            return bool(self.redis_client.delete(key))
        except redis.RedisError:
            return False
    
    def invalidate(self, pattern: str) -> int:
        """Invalidate cache entries matching pattern"""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except redis.RedisError:
            return 0
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        try:
            return bool(self.redis_client.exists(key))
        except redis.RedisError:
            return False
    
    def get_or_set(self, key: str, callable_func, ttl: Optional[int] = None) -> Any:
        """Get from cache or set using callable function"""
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Cache miss - call function and cache result
        fresh_value = callable_func()
        self.set(key, fresh_value, ttl)
        return fresh_value
