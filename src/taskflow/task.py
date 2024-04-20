from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
import inspect
from .cache import CacheProvider, SqliteCacheProvider
from loguru import logger

# import multiprocessing
import concurrent.futures


class Task(ABC):
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache

    @abstractmethod
    def run(self, *args, **kwargs) -> dict[str, Any]:
        pass


def serial_run(tasks: list[Task]) -> dict[str, Any]:
    d: dict[str, Any] = {}
    for task in tasks:
        # get the params list of the task.run
        params = task.run.__code__.co_varnames

        task_params = {}
        for param in params:
            if param == "self":
                continue
            if param in d:
                task_params[param] = d[param]
            else:
                raise ValueError(f"Task parameter {param} not found in the pool")

        result = task.run(**task_params)
        if result is not None:
            # check if result is a [str, Any] dictionary
            if not isinstance(result, dict):
                raise TypeError("Task result must be a dictionary")
            if not all(isinstance(k, str) for k in result.keys()):
                raise TypeError("Task result keys must be strings")

            # key should be unique
            if any(k in d for k in result.keys()):
                raise ValueError("Task result keys must be unique")

            d.update(result)
        # print(d)
    return d


def multiprocess_run(tasks: list[Task]) -> dict[str, Any]:
    executor = concurrent.futures.ProcessPoolExecutor()
    d: dict[str, Any] = {}

    futures: list[concurrent.futures.Future] = []  # list of executing tasks
    d_future_task: dict[concurrent.futures.Future, Task] = {}
    d_task_done = {t: False for t in tasks}

    def is_task_prepared(task: Task):
        params = task.run.__code__.co_varnames
        for param in params:
            if param == "self":
                continue
            if param not in d:
                return False
        return True

    for task in tasks:
        if is_task_prepared(task):
            future = executor.submit(task.run)
            futures.append(future)
            d_future_task[future] = task
            logger.debug(f"submit task {task} in first round")

    while futures:
        # get the task that is done
        def wait_until_any(futures: list[concurrent.futures.Future]):
            for f in concurrent.futures.as_completed(futures):
                return f
            raise ValueError("No task is done")

        future = wait_until_any(futures)
        futures.remove(future)

        result = future.result()
        if result is not None:
            d.update(result)
        t = d_future_task[future]
        d_task_done[t] = True

        for task in tasks:
            if d_task_done[task]:
                continue
            if is_task_prepared(task):
                task_params = {}
                for param in task.run.__code__.co_varnames:
                    if param == "self":
                        continue
                    task_params[param] = d[param]

                future = executor.submit(task.run, **task_params)
                futures.append(future)
                d_future_task[future] = task
                logger.debug(f"submit task {task} by {t}")

    return d


class Pool:
    def __init__(
        self,
        tasks: list[Task],
        cache_provider: Optional[CacheProvider] = None,
        run_func: Callable[[list[Task]], dict[str, Any]] = serial_run,
    ):
        self.tasks = tasks
        self.d: dict[str, Any] = {}
        if cache_provider is None:
            cache_provider = SqliteCacheProvider()
        self.cache_provider = cache_provider
        self.run_func = run_func

    def _execute_task(self, task: Task, params: dict[str, Any]) -> dict[str, Any]:
        print(f"run task {task}, enable_cache: {task.enable_cache}")
        if not task.enable_cache:
            return task.run(**params)

        task_code = inspect.getsource(task.__class__)

        cache_output = self.cache_provider.get(task_code, params)
        if cache_output is not None:
            return cache_output

        output = task.run(**params)
        self.cache_provider.set(task_code, params, output)
        return output

    def run(self):
        return self.run_func(self.tasks)
