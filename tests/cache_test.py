from pathlib import Path
import tasksflow.cache
import tasksflow.task
import tasksflow.pool
from loguru import logger

logger.enable("tasksflow")


def test_provider_valid() -> None:
    sqlite_cache_provider = tasksflow.cache.SqliteCacheProvider(Path("test.db"))

    cache_providers: list[tasksflow.cache.CacheProvider] = [
        sqlite_cache_provider,
        tasksflow.cache.MemoryCacheProvider(),
    ]

    for c in cache_providers:
        logger.info(f"check cache provider {c}")
        assert c._check_valid()

    sqlite_cache_provider.clear()


file_tmp = Path("tmp")


class Task1(tasksflow.task.Task):
    def run(self):
        file_tmp.touch()  # side effect, should not appear when cache is working
        return {"a": 1, "b": 2}


class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}


def test_cache_work():
    """
    Test whether the cache works as expected. Especially in the case of the muliprocess Executor.
    """
    if file_tmp.exists():
        file_tmp.unlink()

    tasks = [Task1(), Task2()]

    mem_cache_provider = tasksflow.cache.MemoryCacheProvider()

    p = tasksflow.pool.Pool(tasks, cache_provider=mem_cache_provider)
    p.run()

    assert file_tmp.exists()
    file_tmp.unlink()

    p.run()
    assert not file_tmp.exists()
