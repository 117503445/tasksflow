# tasksflow

> Handling complex workflows through tasks

English | [简体中文](./README_zh_CN.md)

When dealing with complex workflows, it's often necessary to break them down into multiple tasks and then combine these tasks together. This library provides a simple way to define and execute these tasks.

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

Each task has multiple input parameters and multiple output parameters. Taking Task2 as an example:

```python
class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}
```

Task2 takes input parameters `a` and `b`, and outputs parameter `c`.

Each task needs to inherit from `tasksflow.task.Task` and override the `run` method. The parameters of the `run` method are the inputs required for this task, and the return value should be a dict of parameter->value, ensuring that each task returns non-repeating parameters.

There's no need to explicitly define the dependencies between tasks. Once the parameters returned by the preceding tasks are available, the subsequent tasks that depend on these parameters will be automatically invoked with these values.

### Pool

`tasksflow.pool.Pool` is a pool of tasks used for running a series of tasks. The common usage is:

```python
tasks = [Task1(), Task2()]
p = tasksflow.pool.Pool(tasks)
result = p.run() # run tasks in pool
```

Initialize the task pool using `tasksflow.pool.Pool(tasks)` and execute the task list with `result = p.run()`, obtaining the results as a dict of all tasks' parameter->value.

## Advanced

### Cache

For most tasks, as long as the input parameters and the task code remain the same, the final output result will also be the same. By default, `tasksflow` caches the task code and inputs/outputs. When running the task again and hitting the cache, it skips the execution process and directly uses the output. This caching feature can effectively improve development efficiency, as developers don't need to rerun previous tasks when developing subsequent tasks.

#### Disabling Task Cache

Some tasks rely on external factors such as the network or time, and even with the same input parameters and task code, they may produce different outputs. In such cases, it may be necessary to disable caching and force task execution. This can be achieved by declaring cache disabling during task initialization.

```python
tasks = [Task1(), Task2(enable_cache=False)]
```

Here, Task2 is passed `enable_cache=False`, indicating that caching should be disabled for this task.

#### Cache Implementation

By default, `pool` will create a SQLite database at `cache.db` and cache task codes and inputs. If you want to customize the storage path:

```python
from pathlib import Path
p = tasksflow.pool.Pool(tasks, cache_provider=tasksflow.cache.SqliteCacheProvider(Path("mycache.db")))
```

You can also use `MemoryCacheProvider` instead of `SqliteCacheProvider`, which stores the cache in memory, commonly used for testing.

```python
p = tasksflow.pool.Pool(tasks, cache_provider=tasksflow.cache.MemoryCacheProvider())
```

Or you can customize `CacheProvider` by inheriting `tasksflow.cache.CacheProvider` and implementing the `get` and `set` methods. Then pass your custom `CacheProvider` to the `Pool`.

### Executer

By default, `pool` uses `tasksflow.executer.MultiprocessExecuter`, which creates a separate process for each task. Once a task is completed, it automatically invokes the dependent tasks based on the output of this task.

You can also use `tasksflow.executer.SerialExecuter`, which executes tasks sequentially according to the order in `tasks`.

```python
p = tasksflow.pool.Pool(tasks, executer=tasksflow.executer.SerialExecuter())
```

Or you can create a custom executer.

```python
from typing import Any
class MyExecuter(Executer):
    def run(tasks: list[tasksflow.task.Task]) -> dict[str, Any]:
        pass
p = tasksflow.pool.Pool(tasks, executer=MyExecuter())
```

### Logging

`tasksflow` uses the `loguru` module for logging. You can control whether `tasksflow`'s logs are printed using the following code. By default, `tasksflow`'s logs are disabled.

```python
# install loguru by `pip install loguru`

from loguru import logger
logger.enable("tasksflow")
```

## More Realistic Example

Scrape the titles of the website <https://webscraper.io/test-sites>. Use `tasksflow` to decompose the scraping task into 2 subtasks: web request and web parsing. This way, when developing the web parsing subtask, caching is utilized to avoid requesting the webpage again.

Install dependencies

```sh
pip install tasksflow requests lxml
```

Write the code

```python
import tasksflow.pool
import tasksflow.task
from lxml import etree
import requests


class TaskRequest(tasksflow.task.Task):
    def run(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        }
        url = "https://webscraper.io/test-sites"
        resp = requests.get(url, headers=headers).text
        return {"resp": resp}


class TaskParse(tasksflow.task.Task):
    def run(self, resp: str):
        html = etree.HTML(resp, etree.HTMLParser())
        title_elements = html.xpath("/html/body/div[1]/div[3]/div[*]/div[1]/h2/a")
        titles = [title.text.strip() for title in title_elements]
        return {"titles": titles}


def main():
    tasks = [TaskRequest(), TaskParse()]
    p = tasksflow.pool.Pool(tasks)
    result = p.run()
    print(f"titles: {result['titles']}")
    # titles: ['E-commerce site', 'E-commerce site with pagination links', 'E-commerce site with AJAX pagination links', 'E-commerce site with "Load more" buttons', 'E-commerce site that loads items while scrolling', 'Table playground']


if __name__ == "__main__":
    main()
```

## Development

See [dev_zh_CN.md](./docs/dev_zh_CN.md)
