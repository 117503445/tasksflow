from .common import Payload

from .task import Task
from .cache import CacheProvider
from loguru import logger
import concurrent.futures
from enum import Enum
from typing import Optional
import multiprocessing
from abc import ABC, abstractmethod
import inspect


def _get_task_params_names(task: Task) -> list[str]:
    # https://stackoverflow.com/a/40363565
    fn = task.run
    params = fn.__code__.co_varnames[: fn.__code__.co_argcount]

    ban_set = {"self"}

    names = [param for param in params if param not in ban_set]
    # logger.debug(f"task {task} params: {names}")
    return names


class Executer(ABC):
    def __init__(self, cache_provider: Optional[CacheProvider] = None):
        super().__init__()
        self.cache_provider = cache_provider

    def _get_task_result_from_cache(
        self, task: Task, task_params: Payload
    ) -> Optional[Payload]:
        """
        get task result from cache, return None if not found

        :param task: the task
        :param task_params: the params of the task
        """
        if self.cache_provider is None:
            return None

        task_code = inspect.getsource(task.__class__)
        cache_output = self.cache_provider.get(task_code, task_params)
        return cache_output

    def _set_task_result_to_cache(
        self, task: Task, task_params: Payload, result: Payload
    ):
        """
        set task result to cache

        :param task: the task
        :param task_params: the params of the task
        :param result: the result of the task
        """
        if self.cache_provider is not None:
            task_code = inspect.getsource(task.__class__)
            self.cache_provider.set(task_code, task_params, result)

    @abstractmethod
    def run(self, tasks: list[Task]) -> Payload:
        raise NotImplementedError


class SerialExecuter(Executer):
    def run(self, tasks: list[Task]) -> Payload:
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
                    raise ValueError(
                        f"Task parameter {param} not given by previous tasks"
                    )

            result = self._get_task_result_from_cache(task, task_params)
            if result is None:
                result = task._execute(**task_params)
                self._set_task_result_to_cache(task, task_params, result)

            # key should be unique
            if any(k in d_payload for k in result.keys()):
                raise ValueError("Task result keys must be unique")
            d_payload.update(result)
        return d_payload


class MultiprocessExecuter(Executer):
    def run(self, tasks: list[Task]) -> Payload:
        """
        Execute tasks in parallel using multiprocessing

        :param tasks: list of tasks
        """

        d_payload: Payload = {}  # param -> value

        class TaskStatus(Enum):
            NOT_STARTED = 0
            RUNNING = 1
            DONE = 2

        class RunableTask:
            def __init__(self, task: Task):
                self.task = task
                self.status = TaskStatus.NOT_STARTED
                self.future: Optional[concurrent.futures.Future] = None
                self.task_params: Optional[Payload] = None

            def is_prepared(self):
                """
                Check if the task is ready to be executed
                """

                # if all the parameters are ready, then the task is ready
                for param in _get_task_params_names(self.task):
                    if param not in d_payload:
                        return False
                return True

        rtasks = [RunableTask(task) for task in tasks]

        ctx = multiprocessing.get_context(
            "spawn"
        )  # https://docs.python.org/3/whatsnew/3.12.html#:~:text=101588%20%E4%B8%AD%E8%B4%A1%E7%8C%AE%E3%80%82%EF%BC%89-,multiprocessing,-%3A%20In%20Python%203.14
        with concurrent.futures.ProcessPoolExecutor(mp_context=ctx) as executor:
            futures: list[concurrent.futures.Future] = []  # list of executing tasks

            def _submit_prepared_tasks() -> None:
                """
                submit tasks that are prepared in rtasks

                :param pre_task: the task that triggers the submission
                """
                cache_prepared_tasks: list[
                    RunableTask
                ] = []  # tasks that are prepared by cache
                for rtask in rtasks:
                    if rtask.status == TaskStatus.NOT_STARTED and rtask.is_prepared():
                        task_params = {}
                        for param in _get_task_params_names(rtask.task):
                            task_params[param] = d_payload[param]

                        rtask.task_params = task_params

                        result = self._get_task_result_from_cache(
                            rtask.task, task_params
                        )

                        if result is not None:
                            d_payload.update(result)
                            rtask.status = TaskStatus.DONE
                            cache_prepared_tasks.append(rtask)

                            logger.debug(
                                f"cache hit task: {rtask.task.__class__.__name__}"
                            )
                        else:
                            rtask.status = TaskStatus.RUNNING
                            future = executor.submit(rtask.task._execute, **task_params)
                            futures.append(future)
                            rtask.future = future

                            logger.debug(
                                f"submit task: {rtask.task.__class__.__name__}"
                            )

                if cache_prepared_tasks:
                    _submit_prepared_tasks()

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
                rtask = next(
                    rtask for rtask in rtasks if rtask.future == future
                )  # find rtask by future
                if rtask.task_params is None:
                    raise ValueError(f"rtask {rtask} task_params should not be None")
                self._set_task_result_to_cache(rtask.task, rtask.task_params, result)
                rtask.status = TaskStatus.DONE
                d_payload.update(result)

                _submit_prepared_tasks()

            for rtask in rtasks:
                if rtask.status != TaskStatus.DONE:
                    raise ValueError(f"rtask {rtask} is not done")

        return d_payload
