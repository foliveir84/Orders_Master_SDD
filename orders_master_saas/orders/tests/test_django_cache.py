import pytest
from django.core.cache import cache

from orders_master.integrations.django_cache import django_cache_decorator


@pytest.mark.django_db
def test_cache_decorator_caches_result():
    call_count = 0

    @django_cache_decorator(timeout=300, key_prefix="test_fn")
    def expensive_fn(x):
        nonlocal call_count
        call_count += 1
        return x * 2

    cache.clear()
    result1 = expensive_fn(5)
    assert result1 == 10
    assert call_count == 1

    result2 = expensive_fn(5)
    assert result2 == 10
    assert call_count == 1  # cached, not called again

    result3 = expensive_fn(7)
    assert result3 == 14
    assert call_count == 2  # different args = new call


@pytest.mark.django_db
def test_cache_decorator_key_isolation():
    @django_cache_decorator(timeout=300, key_prefix="iso_test")
    def fn_a(x):
        return x + 1

    @django_cache_decorator(timeout=300, key_prefix="iso_test2")
    def fn_b(x):
        return x + 2

    cache.clear()
    assert fn_a(10) == 11
    assert fn_b(10) == 12