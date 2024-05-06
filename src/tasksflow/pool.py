from .common import Payload
from .task import Task
from loguru import logger
from typing import Any, Optional, Callable
from .cache import CacheProvider, SqliteCacheProvider
from .executer import Executer, SerialExecuter, MultiprocessExecuter
from copy import deepcopy


class Pool:
    def __init__(
        self,
        tasks: list[Task],
        cache_provider: Optional[CacheProvider] = None,
        executer: Optional[Executer] = None,
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
        # if not cache_provider._check_valid():
        #     raise ValueError(
        #         "Cache provider is not valid, please ensure cache_provider._check_valid() returns True"
        #     )



        # for task in self.tasks:
        #     task.cache_provider = cache_provider
        if executer is None:
            # executer = SerialExecuter(cache_provider=cache_provider)
            executer = MultiprocessExecuter(cache_provider=cache_provider)
        self.executer = executer

    def run(self):
        """
        Execute the tasks in the pool
        """
        return self.executer.run(self.tasks)
