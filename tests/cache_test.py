import tasksflow.cache
from pathlib import Path


def test_case1():
    c = tasksflow.cache.SqliteCacheProvider(Path("test.db"))
    assert c._check_valid()

    c = tasksflow.cache.MemoryCacheProvider()
    assert c._check_valid()
