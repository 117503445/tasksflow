import sqlite3
import pickle
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path
from .common import Code, Payload, PayloadBin
from loguru import logger


class CacheProvider(ABC):
    @abstractmethod
    def get(self, code: Code, params: Payload) -> Optional[Payload]:
        '''
        get result for code and params from cache, return None if not found

        :param code: the code of the task
        :param params: the params of the task
        '''
        raise NotImplementedError

    @abstractmethod
    def set(self, code: Code, params: Payload, result: Payload):
        '''
        set result cache for code and params

        :param code: the code of the task
        :param params: the params of the task
        :param result: the result of the task
        '''
        raise NotImplementedError

    @abstractmethod
    def clear(self, remain_records: int = 0):
        '''
        clear cache, if remain_records is 0, clear all cache records

        :param remain_records: the number of records to remain
        '''
        raise NotImplementedError

    def _check_valid(self) -> bool:
        '''
        check if the cache provider is valid
        '''
        result = {"c": 3}
        self.set("task1", {"a": 1, "b": 2}, result)
        cache_result = self.get("task1", {"a": 1, "b": 2})
        if cache_result is None:
            return False
        if cache_result != result:
            return False
        self.clear()
        cache_result = self.get("task1", {"a": 1, "b": 2})
        return cache_result is None


class MemoryCacheProvider(CacheProvider):
    def __init__(self: "MemoryCacheProvider"):
        self.d: dict[tuple[Code, PayloadBin], Payload] = {}

    def get(self, code: Code, params: Payload) -> Optional[Payload]:
        params_bin = pickle.dumps(params)
        return self.d.get((code, params_bin))

    def set(self, code: Code, params: Payload, result: Payload):
        params_bin = pickle.dumps(params)
        self.d[(code, params_bin)] = result

    def clear(self, remain_records: int = 0):
        if remain_records < 0:
            raise ValueError("remain_records must be greater than or equal to 0")
        if remain_records == 0:
            self.d.clear()
        else:
            self.d = dict(list(self.d.items())[-remain_records:])


class SqliteCacheProvider(CacheProvider):
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path("cache.db")
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

    def get(self, code: str, params: Payload) -> Optional[Payload]:
        if not self.db_path.exists():
            self._create_db()

        params_bin = pickle.dumps(params)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "SELECT result FROM cache WHERE code = ? AND params = ?",
                (code, params_bin),
            )
            record = c.fetchone()
            if record is None:
                return None
            result = pickle.loads(record[0])
            return result

    def set(self, code: str, params: Payload, result: Payload):
        logger.debug(f"set cache for code: {code}, params: {params}, result: {result}")
        if not self.db_path.exists():
            self._create_db()

        params_bin = pickle.dumps(params)
        result_bin = pickle.dumps(result)

        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR REPLACE INTO cache (code, params, result) VALUES (?, ?, ?)",
                (code, params_bin, result_bin),
            )

            conn.commit()

    def clear(self, remain_records: int = 0):
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
