import taskflow.cache
from pathlib import Path


def test_case1():
    c = taskflow.cache.SqliteCacheProvider(Path("test.db"))
    assert c._check_valid()

    c = taskflow.cache.MemoryCacheProvider()
    assert c._check_valid()
