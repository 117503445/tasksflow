from abc import ABC, abstractmethod
from typing import Any
import inspect
import sqlite3
from pathlib import Path


class Task(ABC):
    def __init__(self, enable_cache: bool = True):
        self.enable_cache = enable_cache

    @abstractmethod
    def run(self, *args, **kwargs) -> dict[str, Any]:
        pass


class Pool:
    def __init__(self, tasks: list[Task]):
        self.tasks = tasks
        self.d: dict[str, Any] = {}

    def _execute_task(self, task: Task, params: dict[str, Any]) -> dict[str, Any]:
        print(f"run task {task}, enable_cache: {task.enable_cache}")
        if not task.enable_cache:
            return task.run(**params)

        # get the task code
        task_code = inspect.getsource(task.__class__)
        print(f"task_code: {task_code}")

        return task.run(**params)

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


class Cache(ABC):

    @abstractmethod
    def get(self, code: str, params: dict[str, Any]) -> dict[str, Any] | None:
        pass

    @abstractmethod
    def set(self, code: str, params: dict[str, Any], result: dict[str, Any]):
        pass

    @abstractmethod
    def clear(self, remain_records: int):
        pass


class SqliteCache(Cache):
    def __init__(self, db_path: Path):
        self.db_path = db_path

    def _create_db(self):
        if self.db_path.exists():
            return
        
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # unique constraint (code, params)
            c.execute(
                "CREATE TABLE cache (code TEXT, params TEXT, result TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, UNIQUE(code, params))"
            )
            conn.commit()

    def get(self, code: str, params: dict[str, Any]) -> dict[str, Any] | None:
        if not self.db_path.exists():
            self._create_db()

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT result FROM cache WHERE code = ? AND params = ?",
                (code, str(params)),
            )
            result = c.fetchone()
            if result is None:
                return None
            return result

    def set(self, code: str, params: dict[str, Any], result: dict[str, Any]):
        if not self.db_path.exists():
            self._create_db()

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO cache (code, params, result) VALUES (?, ?, ?)",
                (code, str(params), str(result)),
            )

            conn.commit()

    def clear(self, remain_records: int):
        if remain_records < 0:
            raise ValueError("remain_records must be greater than or equal to 0")

        if not self.db_path.exists():
            return

        if remain_records == 0:
            self.db_path.unlink()
            return

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "DELETE FROM cache WHERE ROWID NOT IN (SELECT ROWID FROM cache ORDER BY created_at DESC LIMIT ?)",
                (remain_records,),
            )
            conn.commit()
