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
    # pool = multiprocessing.Pool()
    executor = concurrent.futures.ProcessPoolExecutor()
    d: dict[str, Any] = {}

    d_param_task: dict[str, Task] = {}
    for task in tasks:
        params = task.run.__code__.co_varnames
        for param in params:
            if param == "self":
                continue
            if param in d_param_task:
                raise ValueError(f"Task parameter {param} is duplicated")
            d_param_task[param] = task

    logger.debug(f"d_param_task: {d_param_task}")

    dag: dict[Task, set[Task]] = {}  # task -> dependent tasks
    for task in tasks:
        dag[task] = set()
        params = task.run.__code__.co_varnames
        for param in params:
            if param == "self":
                continue
            dag[task].add(d_param_task[param])

    logger.debug(f"dag: {dag}")

    futures = []

    d_future_task: dict[concurrent.futures.Future, Task] = {}
    d_task_done = {t: False for t in tasks}

    for task in dag:
        if not dag[task]:
            future = executor.submit(task.run)
            d_future_task[future] = task
            logger.debug(f"submit task {task} in first round")
            futures.append(future)

    while futures:
        # get the task that is done
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            d.update(result)
            task = d_future_task[future]
            d_task_done[task] = True
            for dep_task in dag[task]:
                if (
                    all(d_task_done[dep_task] for dep_task in dag[task])
                    and not d_task_done[dep_task]
                ):
                    future = executor.submit(dep_task.run, **d)
                    d_future_task[future] = dep_task
                    futures.append(future)

            futures.remove(future)
            break

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
