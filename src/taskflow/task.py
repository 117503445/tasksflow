from abc import ABC, abstractmethod
from typing import Any


class Task(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run(self, *args, **kwargs) -> dict[str, Any]:
        pass


class Pool:
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.d = {}

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
            
            result = task.run(**task_params)
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
            print(self.d)
