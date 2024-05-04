import tasksflow.cache
from pathlib import Path


def test_case1() -> None:
    cache_providers: list[tasksflow.cache.CacheProvider] = [
        tasksflow.cache.SqliteCacheProvider(Path("test.db")),
        tasksflow.cache.MemoryCacheProvider(),
    ]

    for c in cache_providers:
        assert c._check_valid()
