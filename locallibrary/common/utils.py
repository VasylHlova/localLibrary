from typing  import Any

from django.core.paginator import Paginator, Page
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


from typing import Any
from django.core.paginator import Paginator, Page
from django.core.cache import cache

class VersionedCacheListMixin:
    cache_timeout = 60 * 60 
    cache_key_prefix = None 

    def _get_model(self):
        model = getattr(self, 'model', None)
        if model:
            return model
        
        queryset = getattr(self, 'queryset', None)
        if queryset is not None:
            return queryset.model
        
        return self.get_queryset().model

    def get_cache_prefix(self) -> str:
        model = self._get_model()
        model_name = model._meta.model_name
        return self.cache_key_prefix or f"{model_name}_list"

    def paginate_queryset(self, queryset, page_size) -> tuple[Paginator, Page, list[Any], bool]:
        page_kwarg = self.page_kwarg
        page_number = self.kwargs.get(page_kwarg) or self.request.GET.get(page_kwarg) or 1
        
        prefix = self.get_cache_prefix()
        model = self._get_model()
        model_name = model._meta.model_name
        version = get_model_cache_version(model_name)
        
        cache_key = f"{prefix}_p{page_number}_v{version}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        paginator, page, object_list, is_paginated = super().paginate_queryset(queryset, page_size)
        
        evaluated_object_list = list(object_list)
        page.object_list = evaluated_object_list
        result_tuple = (paginator, page, evaluated_object_list, is_paginated)
        
        cache.set(cache_key, result_tuple, self.cache_timeout)
        
        return result_tuple
    

