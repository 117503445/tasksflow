from abc import ABC, abstractmethod


class Task(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run(self):
        pass


class Pool:
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.d = {}

    def run(self):
        for task in self.tasks:
            task.run()
