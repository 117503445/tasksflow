import tasksflow.cache
import tasksflow.task
import tasksflow.executer
import tasksflow.pool

from loguru import logger
import time


def heavy_cpu_work(t: float):
    """
    execute cpu intensive work, until t seconds
    """
    start = time.time()
    while time.time() - start < t:
        i = 0
        for _ in range(100000):
            i += 1
    # logger.debug(f"heavy_cpu_work for {time.time() - start} seconds")


class Task1(tasksflow.task.Task):
    def run(self):
        heavy_cpu_work(0.5)
        return {"a": 1, "b": 2}


class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        heavy_cpu_work(0.5)
        return {"c": a + b}


class Task3(tasksflow.task.Task):
    def run(self, c: int):
        heavy_cpu_work(2)


class Task4(tasksflow.task.Task):
    def run(self, c: int):
        heavy_cpu_work(2)


def test_multiprocess_run_speedup():
    # get the number of cpu cores
    import multiprocessing

    num_cores = multiprocessing.cpu_count()
    if num_cores <= 1:
        logger.warning("The number of cpu cores is less than 2, skip the test")
        return

    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.pool.Pool(
        tasks,
        executer=tasksflow.executer.serial_run,
        cache_provider=tasksflow.cache.MemoryCacheProvider(),
    )
    start = time.time()
    result = p.run()
    serial_time = time.time() - start

    assert result == {"a": 1, "b": 2, "c": 3}
    assert serial_time > 5

    p = tasksflow.pool.Pool(
        tasks,
        executer=tasksflow.executer.multiprocess_run,
        cache_provider=tasksflow.cache.MemoryCacheProvider(),
    )

    start = time.time()
    result = p.run()
    multiprocess_time = time.time() - start

    assert result == {"a": 1, "b": 2, "c": 3}
    assert multiprocess_time < 4 # 0.5 + 0.5 + 2 = 3
