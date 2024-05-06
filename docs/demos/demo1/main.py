import tasksflow.pool
import tasksflow.task
import tasksflow.cache

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



def main():

    mem = tasksflow.cache.MemoryCacheProvider()

    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.pool.Pool(tasks, cache_provider=mem)
    result = p.run()
    print(f"result: {result}")
    result = p.run()
    print(f"result: {result}")


if __name__ == "__main__":
    main()
