import inspect
from abc import ABC, abstractmethod
from typing import Any, Optional, Callable
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
            if not kwargs:
                kwargs = {}
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


