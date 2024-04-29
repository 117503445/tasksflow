import inspect
import concurrent.futures
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
from enum import Enum
from copy import deepcopy
from .cache import CacheProvider, SqliteCacheProvider
from .common import Payload
from loguru import logger


class Task(ABC):
    def __init__(self, enable_cache: bool = True):
        """
        Task is the base class for all tasks

        :param enable_cache: whether to enable cache for the task
        """
        self.enable_cache = enable_cache
        self.cache_provider: Optional[CacheProvider] = None

    @abstractmethod
    def run(self, *args, **kwargs) -> Optional[Payload]:
        """
        user-defined task logic, should return a dict[str, Any] or None
        """
        raise NotImplementedError

    def _execute(self, *args, **kwargs):
        """
        execute the task, if cache_provider is not None, cache the result
        """
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
            logger.debug(f"execute task {self}, args: {args}, kwargs: {kwargs}")
            output = self.run(*args, **kwargs)
            if output is None:
                output = {}
            self.cache_provider.set(task_code, kwargs, output)
            return output


def _get_task_params_names(task: Task) -> list[str]:
    # https://stackoverflow.com/a/40363565
    fn = task.run
    params = fn.__code__.co_varnames[: fn.__code__.co_argcount]

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


def serial_run(tasks: list[Task]) -> Payload:
    """
    serially execute tasks

    :param tasks: list of tasks
    """
    d_payload: Payload = {}
    for task in tasks:
        # try to get all the parameters for the task
        task_params: Payload = {}
        for param in _get_task_params_names(task):
            if param in d_payload:
                task_params[param] = d_payload[param]
            else:
                raise ValueError(f"Task parameter {param} not given by previous tasks")

        result = task._execute(**task_params)
        if result is not None:
            # result should be valid payload
            if not _is_payload_valid(result):
                raise ValueError(
                    f"Task result must be a dict[str, Any] or None, but get {result} for task {task}"
                )

            # key should be unique
            if any(k in d_payload for k in result.keys()):
                raise ValueError("Task result keys must be unique")

            d_payload.update(result)
    return d_payload


def multiprocess_run(tasks: list[Task]) -> Payload:
    """
    Execute tasks in parallel using multiprocessing

    :param tasks: list of tasks
    """

    d_payload: Payload = {}  # param -> value
    with concurrent.futures.ProcessPoolExecutor() as executor:
        futures: list[concurrent.futures.Future] = []  # list of executing tasks
        d_future_task: dict[concurrent.futures.Future, Task] = {}  # future -> task

        class TaskStatus(Enum):
            NOT_STARTED = 0
            RUNNING = 1
            DONE = 2

        d_task_status = {t: TaskStatus.NOT_STARTED for t in tasks}

        def is_task_prepared(task: Task):
            """
            Check if the task is ready to be executed
            """

            # if all the parameters are ready, then the task is ready
            for param in _get_task_params_names(task):
                if param not in d_payload:
                    return False
            return True

        def _submit_prepared_tasks(pre_task: Optional[Task] = None):
            """
            submit tasks that are prepared

            :param pre_task: the task that triggers the submission
            """
            for task in tasks:
                if d_task_status[task] == TaskStatus.NOT_STARTED and is_task_prepared(
                    task
                ):
                    task_params = {}
                    for param in _get_task_params_names(task):
                        task_params[param] = d_payload[param]

                    future = executor.submit(task._execute, **task_params)
                    d_task_status[task] = TaskStatus.RUNNING
                    futures.append(future)
                    d_future_task[future] = task
                    if pre_task is not None:
                        logger.debug(f"submit task {task} by {pre_task}")
                    else:
                        logger.debug(f"submit task {task}")

        # get the task that is done
        def wait_until_any(futures: list[concurrent.futures.Future]):
            for f in concurrent.futures.as_completed(futures):
                return f
            raise ValueError("No task is done")

        _submit_prepared_tasks()
        while futures:
            future = wait_until_any(futures)
            futures.remove(future)

            result = future.result()
            task = d_future_task[future]
            d_task_status[task] = TaskStatus.DONE
            if result is not None:
                if not _is_payload_valid(result):
                    raise ValueError(
                        f"Task result must be a dict[str, Any] or None, but get {result} for task {task}"
                    )
                d_payload.update(result)

            _submit_prepared_tasks(task)

    return d_payload


class Pool:
    def __init__(
        self,
        tasks: list[Task],
        cache_provider: Optional[CacheProvider] = None,
        executer: Callable[[list[Task]], Payload] = serial_run,
    ):
        """
        Pool of tasks

        :param tasks: list of tasks
        :param cache_provider: cache task execution result to avoid re-execution for the same input
        :param executer: function to execute tasks
        """

        # use deepcopy to prevent tasks from being modified
        self.tasks = deepcopy(tasks)

        if cache_provider is None:
            cache_provider = SqliteCacheProvider()
            # cache_provider = MemoryCacheProvider()
        if not cache_provider._check_valid():
            raise ValueError(
                "Cache provider is not valid, please ensure cache_provider._check_valid() returns True"
            )
        self.cache_provider = cache_provider

        for task in self.tasks:
            task.cache_provider = self.cache_provider

        self.executer = executer

    def run(self):
        """
        Execute the tasks in the pool
        """
        return self.executer(self.tasks)
