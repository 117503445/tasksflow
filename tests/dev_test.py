import tasksflow.task
from loguru import logger


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


def test_case1():
    logger.debug("test_case1 start")
    tasks = [Task1(), Task2(), Task3()]
    p = tasksflow.task.Pool(tasks)
    # p = tasksflow.task.Pool(tasks, run_func=tasksflow.task.multiprocess_run)
    result = p.run()

    logger.debug(f"result: {result}")
    logger.debug("test_case1 end")


def test_case2():
    logger.debug("test_case2 start")
    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.task.Pool(tasks, run_func=tasksflow.task.multiprocess_run)
    # p = tasksflow.task.Pool(tasks)
    result = p.run()

    logger.debug(f"result: {result}")
    logger.debug("test_case2 end")
