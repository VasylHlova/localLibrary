import pytest
from unittest.mock import MagicMock
from django.db.models import QuerySet
from common.pagination import CustomPageNumberPagination

def test_custom_pagination_count_under_max():
    paginator = CustomPageNumberPagination()
    qs = MagicMock(spec=QuerySet)
    
    values_qs = MagicMock()
    sliced_qs = MagicMock()
    sliced_qs.count.return_value = 500
    
    values_qs.__getitem__.return_value = sliced_qs
    qs.values.return_value = values_qs
    
    assert paginator.get_count(qs) == 500
    qs.values.assert_called_once_with('pk')
    values_qs.__getitem__.assert_called_once_with(slice(None, 10000, None))

def test_custom_pagination_count_at_max():
    paginator = CustomPageNumberPagination()
    qs = MagicMock(spec=QuerySet)
    
    values_qs = MagicMock()
    sliced_qs = MagicMock()
    sliced_qs.count.return_value = 10000
    
    values_qs.__getitem__.return_value = sliced_qs
    qs.values.return_value = values_qs
    
    assert paginator.get_count(qs) == 10000
