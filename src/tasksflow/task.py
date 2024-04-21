from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
import inspect
from .cache import CacheProvider, SqliteCacheProvider, MemoryCacheProvider
from loguru import logger

# import multiprocessing
import concurrent.futures

from .common import Code, Payload, PayloadBin
from enum import Enum
from copy import deepcopy


class Task(ABC):
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache
        self.cache_provider: Optional[CacheProvider] = None

    @abstractmethod
    def run(self, *args, **kwargs) -> dict[str, Any]:
        raise NotImplementedError

    def _execute(self, *args, **kwargs):
        logger.debug(f"execute task {self}, args: {args}, kwargs: {kwargs}")
        if self.cache_provider is None:
            return self.run(*args, **kwargs)
        else:
            task_code = inspect.getsource(self.__class__)
            cache_output = self.cache_provider.get(task_code, kwargs)
            if cache_output is not None:
                logger.debug(f"cache hit for task {self}")
                return cache_output

            logger.debug(f"cache miss for task {self}")
            output = self.run(*args, **kwargs)
            if output is None:
                output = {}
            self.cache_provider.set(task_code, kwargs, output)
            return output


def _get_task_params_names(task: Task) -> list[str]:
    params = task.run.__code__.co_varnames

    ban_set = {"self"}

    names = [param for param in params if param not in ban_set]
    logger.debug(f"task {task} params: {names}")
    return names


def _is_payload_valid(payload: Payload) -> bool:
    if payload is None:
        return False
    if not isinstance(payload, dict):
        return False
    if not all(isinstance(k, str) for k in payload.keys()):
        return False
    return True


def serial_run(tasks: list[Task]) -> dict[str, Any]:
    d_payload: dict[str, Any] = {}
    for task in tasks:
        task_params = {}
        for param in _get_task_params_names(task):
            if param in d_payload:
                task_params[param] = d_payload[param]
            else:
                raise ValueError(f"Task parameter {param} not given by previous tasks")

        result = task._execute(**task_params)
        if result is not None:
            if not _is_payload_valid(result):
                raise ValueError(f"Task result must be a dict[str, Any] or None, but get {result} for task {task}")

            # key should be unique
            if any(k in d_payload for k in result.keys()):
                raise ValueError("Task result keys must be unique")

            d_payload.update(result)
    return d_payload


def multiprocess_run(tasks: list[Task]) -> dict[str, Any]:
    d: dict[str, Any] = {}
    with concurrent.futures.ProcessPoolExecutor() as executor:

        futures: list[concurrent.futures.Future] = []  # list of executing tasks
        d_future_task: dict[concurrent.futures.Future, Task] = {}

        class TaskStatus(Enum):
            NOT_STARTED = 0
            RUNNING = 1
            DONE = 2

        d_task_status = {t: TaskStatus.NOT_STARTED for t in tasks}

        def is_task_prepared(task: Task):
            for param in _get_task_params_names(task):
                if param not in d:
                    return False
            return True

        for task in tasks:
            if is_task_prepared(task):
                future = executor.submit(task._execute)
                d_task_status[task] = TaskStatus.RUNNING
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
                if not _is_payload_valid(result):
                    raise ValueError(f"Task result must be a dict[str, Any] or None, but get {result} for task {task}")
                d.update(result)
                
            t = d_future_task[future]
            d_task_status[t] = TaskStatus.DONE

            for task in tasks:
                if d_task_status[task] != TaskStatus.NOT_STARTED:
                    continue
                if is_task_prepared(task):
                    task_params = {}
                    for param in _get_task_params_names(task):
                        task_params[param] = d[param]

                    future = executor.submit(task._execute, **task_params)
                    d_task_status[task] = TaskStatus.RUNNING
                    futures.append(future)
                    d_future_task[future] = task
                    logger.debug(f"submit task {task} by {t}")

    return d


class Pool:
    def __init__(
        self,
        tasks: list[Task],
        cache_provider: Optional[CacheProvider] = None,
        run_func: Callable[[list[Task]], Payload] = serial_run,
    ):
        # use deepcopy to prevent tasks from being modified
        self.tasks = deepcopy(tasks)

        if cache_provider is None:
            cache_provider = SqliteCacheProvider()
            # cache_provider = MemoryCacheProvider()
        self.cache_provider = cache_provider

        for task in self.tasks:
            task.cache_provider = self.cache_provider

        self.run_func = run_func

    def run(self):
        return self.run_func(self.tasks)
