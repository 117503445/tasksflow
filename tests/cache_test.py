import taskflow.cache
from pathlib import Path


def test_case1():
    c = taskflow.cache.SqliteCacheProvider(Path("test.db"))
    result = {"c": 3}
    c.set("task1", {"a": 1, "b": 2}, result)

    cache_result = c.get("task1", {"a": 1, "b": 2})
    print("cache_result", cache_result, type(cache_result))

    c.clear()
