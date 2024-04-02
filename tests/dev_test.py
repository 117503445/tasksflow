import taskflow.task


class Task1(taskflow.task.Task):
    def run(self):
        print(f"run task1")


class Task2(taskflow.task.Task):
    def run(self):
        print(f"run task2")


def test_case1():
    tasks = [Task1(), Task2()]
    p = taskflow.task.Pool(tasks)
    p.run()
