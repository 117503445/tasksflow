from .common import Payload
from .task import Task
from loguru import logger
from typing import Any, Optional, Callable
from .cache import CacheProvider, SqliteCacheProvider
from .executer import multiprocess_run
from copy import deepcopy

class Pool:
    def __init__(
        self,
        tasks: list[Task],
        cache_provider: Optional[CacheProvider] = None,
        executer: Callable[[list[Task]], Payload] = multiprocess_run,
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
