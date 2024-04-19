from abc import ABC, abstractmethod
from typing import Any, Optional
import inspect
from .cache import CacheProvider, SqliteCacheProvider


class Task(ABC):
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache

    @abstractmethod
    def run(self, *args, **kwargs) -> dict[str, Any]:
        pass


class Pool:
    def __init__(
        self, tasks: list[Task], cache_provider: Optional[CacheProvider] = None
    ):
        self.tasks = tasks
        self.d: dict[str, Any] = {}
        if cache_provider is None:
            cache_provider = SqliteCacheProvider()
        self.cache_provider = cache_provider

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
        for task in self.tasks:
            # get the params list of the task.run
            params = task.run.__code__.co_varnames

            task_params = {}
            for param in params:
                if param == "self":
                    continue
                if param in self.d:
                    task_params[param] = self.d[param]
                else:
                    raise ValueError(f"Task parameter {param} not found in the pool")

            result = self._execute_task(task, task_params)
            if result is not None:
                # check if result is a [str, Any] dictionary
                if not isinstance(result, dict):
                    raise TypeError("Task result must be a dictionary")
                if not all(isinstance(k, str) for k in result.keys()):
                    raise TypeError("Task result keys must be strings")

                # key should be unique
                if any(k in self.d for k in result.keys()):
                    raise ValueError("Task result keys must be unique")

                self.d.update(result)
            # print(self.d)
        return self.d
