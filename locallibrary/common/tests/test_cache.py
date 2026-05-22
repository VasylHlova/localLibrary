from unittest.mock import MagicMock, patch

from common.cache import (
    DRFUserVersionedCacheListMixin,
    DRFVersionedCacheListMixin,
    get_model_cache_version,
    increment_model_cache_version,
)


@patch("common.cache.cache")
def test_get_model_cache_version(mock_cache):
    mock_cache.get_or_set.return_value = 1
    version = get_model_cache_version("testmodel")
    mock_cache.get_or_set.assert_called_once_with("testmodel_cache_version", 1, timeout=None)
    assert version == 1


@patch("common.cache.cache")
def test_increment_model_cache_version(mock_cache):
    increment_model_cache_version("testmodel")
    mock_cache.incr.assert_called_once_with("testmodel_cache_version")


@patch("common.cache.cache")
def test_increment_model_cache_version_value_error(mock_cache):
    mock_cache.incr.side_effect = ValueError()
    increment_model_cache_version("testmodel")
    mock_cache.set.assert_called_once_with("testmodel_cache_version", 1, timeout=None)


def test_drf_versioned_cache_list_mixin():
    mixin = DRFVersionedCacheListMixin()
    request = MagicMock()
    key = mixin._build_cache_key(request, "book", 1, "hash123")
    assert key == "api_book_list_v1_hash123"


def test_drf_user_versioned_cache_list_mixin_authenticated():
    mixin = DRFUserVersionedCacheListMixin()
    request = MagicMock()
    request.user.is_authenticated = True
    request.user.id = 42
    key = mixin._build_cache_key(request, "book", 1, "hash123")
    assert key == "api_book_list_v1_user_42_hash123"


def test_drf_user_versioned_cache_list_mixin_anonymous():
    mixin = DRFUserVersionedCacheListMixin()
    request = MagicMock()
    request.user.is_authenticated = False
    key = mixin._build_cache_key(request, "book", 1, "hash123")
    assert key == "api_book_list_v1_user_anonymous_hash123"
