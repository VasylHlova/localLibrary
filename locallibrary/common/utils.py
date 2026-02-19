from typing  import Any

from django.core.cache import cache

def get_model_cache_version(model_name:str) -> int:

    version_key = f"{model_name}_cache_version"
    return cache.get_or_set(version_key, 1, timeout=None)


def increment_model_cache_version(model_name: str) -> None:
    version_key = f"{model_name}_cache_version"
    try:
        cache.incr(version_key)
    except ValueError:
        cache.set(version_key, 1, timeout=None)


class VersionedCacheListMixin:
    cache_timeout = 60 * 60 
    cache_key_prefix = None 

    def get_cache_key(self) -> str:
        model_name = self.model._meta.model_name
        prefix = self.cache_key_prefix or f"{model_name}_list"
        
        version = get_model_cache_version(model_name)
        
        return f"{prefix}_v{version}"

    def get_queryset(self) -> list[Any]:
        cache_key = self.get_cache_key()
        qs = cache.get(cache_key)
        
        if qs is None:
            qs = list(super().get_queryset())
            cache.set(cache_key, qs, self.cache_timeout)
            
        return qs