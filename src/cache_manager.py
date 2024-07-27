from functools import lru_cache, wraps
from quart import request, current_app


class CacheManager:
    def __init__(self, max_size=None):
        self.max_size = max_size
        self.cache = lru_cache(maxsize=max_size)(lambda k: k)() if max_size else None

    def cache_key(self):
        return request.url

    def get(self, key):
        return self.cache.get(key) if self.cache else None

    def set(self, key, value):
        if self.cache:
            self.cache[key] = value


def cache_response(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        if request.method != 'GET' or not current_app.config['CACHING_ENABLED']:
            return await func(*args, **kwargs)

        cache_manager = current_app.cache_manager
        key = cache_manager.cache_key()
        response = cache_manager.get(key)

        if response is None:
            response = await func(*args, **kwargs)
            cache_manager.set(key, response)

        return response

    return wrapper
