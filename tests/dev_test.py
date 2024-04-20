import taskflow.task


class Task1(taskflow.task.Task):
    def run(self):
        print(f"run task1")
        return {"a": 1, "b": 2}


class Task2(taskflow.task.Task):
    def run(self, a: int, b: int):
        print(f"run task2")
        return {"c": a + b}


class Task3(taskflow.task.Task):
    def run(self, c: int):
        print(f"run task3")
        print(f"c = {c}")


def test_case1():
    tasks = [Task1(), Task2(), Task3()]


    p = taskflow.task.Pool(tasks, run_func=taskflow.task.multiprocess_run)
    result = p.run()
    print('result', result)
