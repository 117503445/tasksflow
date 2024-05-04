# tasksflow

> Handling Complex Workflows with Tasks

When dealing with complex workflows, it's often necessary to decompose them into multiple tasks and then combine these tasks together. This library provides a simple way to define and execute these tasks.

## Quick Start

Install tasksflow

```bash
pip install tasksflow
```

Create some simple tasks

```python
import tasksflow.pool
import tasksflow.task
import tasksflow.cache
import tasksflow.executer
from pathlib import Path

class Task1(tasksflow.task.Task):
    def run(self):
        return {"a": 1, "b": 2}

class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}

tasks = [Task1(), Task2()]
p = tasksflow.pool.Pool(tasks)
result = p.run() # run tasks in pool
print(result) # {"a": 1, "b": 2, "c": 3}
```

## Usage

### Task

Each task has multiple input parameters and multiple output parameters. For example, take Task2:

```python
class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}
```

Task2 takes input parameters `a` and `b`, and outputs parameter `c`.

Each task needs to inherit from `tasksflow.task.Task` and override the `run` method. The parameters of the `run` method are the inputs required for this task, and the return value should be a dict of parameter -> value or None. Make sure that each task returns non-repetitive parameters.

There's no need to explicitly define the dependency relationship between tasks. Once the preceding task returns the values corresponding to the parameters, the subsequent tasks that depend on these parameters will be automatically invoked with these values.

### Pool

`tasksflow.pool.Pool` is a pool of tasks used to run a series of tasks. Common usage:

```python
tasks = [Task1(), Task2()]
p = tasksflow.pool.Pool(tasks)
result = p.run() # run tasks in pool
```

Initialize the pool using `tasksflow.pool.Pool(tasks)`, then execute the list of tasks with `result = p.run()` and retrieve the results. The result is a dict containing the parameter -> value mapping for all tasks.

## Advanced

### Cache

For most tasks, if the input parameters and the task code are the same, the output result will also be the same. By default, `tasksflow` caches the code and inputs/outputs of tasks. When running tasks again and hitting the cache, the execution process is skipped, and the output is directly used. The caching feature can effectively improve development efficiency, as developers don't need to rerun preceding tasks when developing subsequent tasks.

#### Disabling Task Cache

Some tasks may depend on external factors such as the network or time, and even if the input parameters and task code are the same, the results may differ. In such cases, you may need to disable caching to force task execution. This can be done by declaring cache disable during task initialization.

```python
tasks = [Task1(), Task2(enable_cache=False)]
```

Where Task2 is passed `enable_cache=False`, disabling automatic caching.

#### Cache Implementation

By default, the `pool` will create a SQLite database at `cache.db` to cache the task code and inputs. If you want to customize the storage path:

```python
from pathlib import Path
p = tasksflow.pool.Pool(tasks, cache_provider=tasksflow.cache.SqliteCacheProvider(Path("mycache.db")))
```

You can also use `MemoryCacheProvider` instead of `SqliteCacheProvider` to store the cache in memory, commonly used for testing:

```python
p = tasksflow.pool.Pool(tasks, cache_provider=tasksflow.cache.MemoryCacheProvider())
```

Or you can customize the `CacheProvider` by inheriting from `tasksflow.cache.CacheProvider` and implementing the `get` and `set` methods. Then pass your custom `CacheProvider` to the `Pool`.

### Executer

By default, the `pool` uses `tasksflow.executer.multiprocess_run`, which creates a separate process for each task. After a task is completed, it automatically invokes the subsequent tasks that depend on it based on its output.

You can also use `tasksflow.executer.serial_run`, which executes tasks in the order specified.

```python
p = tasksflow.pool.Pool(tasks, executer=tasksflow.executer.serial_run)
```

You can also define your own executor:

```python
from typing import Any
def my_executer(tasks: list[tasksflow.task.Task]) -> dict[str, Any]:
    pass
p = tasksflow.pool.Pool(tasks, executer=my_executer)
```
