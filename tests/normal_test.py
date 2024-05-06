import tasksflow.cache
import tasksflow.executer
import tasksflow.pool
import tasksflow.task
from loguru import logger

logger.enable("tasksflow")


class Task1(tasksflow.task.Task):
    def run(self):
        return {"a": 1, "b": 2}


class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}


class Task3(tasksflow.task.Task):
    def run(self, c: int):
        pass


class Task4(tasksflow.task.Task):
    def run(self, c: int):
        pass

class Task5(tasksflow.task.Task):
    def run(self, un_given: int):
        pass


def test_serial_run():
    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.pool.Pool(
        tasks,
        executer=tasksflow.executer.SerialExecuter(),
        cache_provider=tasksflow.cache.MemoryCacheProvider(),
    )
    result = p.run()

    assert result == {"a": 1, "b": 2, "c": 3}


def test_multiprocess_run():
    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.pool.Pool(
        tasks,
        executer=tasksflow.executer.MultiprocessExecuter(),
        cache_provider=tasksflow.cache.MemoryCacheProvider(),
    )
    result = p.run()

    assert result == {"a": 1, "b": 2, "c": 3}

def test_multiprocess_run_with_un_given():
    tasks = [Task1(), Task2(), Task5()]
    p = tasksflow.pool.Pool(
        tasks,
        executer=tasksflow.executer.MultiprocessExecuter(),
        cache_provider=tasksflow.cache.MemoryCacheProvider(),
    )
    try:
        p.run()
        raise Exception("Should raise an exception when Task5 not executed")
    except Exception as e:
        pass