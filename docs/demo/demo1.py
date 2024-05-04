import tasksflow.pool
import tasksflow.task


class Task1(tasksflow.task.Task):
    def run(self):
        return {"a": 1, "b": 2}


class Task2(tasksflow.task.Task):
    def run(self, a: int, b: int):
        return {"c": a + b}


class Task3(tasksflow.task.Task):
    def run(self, c: int):
        pass


class Task4(tasksflow.task.Task):
    def run(self, c: int):
        pass


def test_case1():
    tasks = [Task1(), Task2(), Task3()]
    p = tasksflow.pool.Pool(tasks)
    result = p.run()
    print(f"result: {result}")


def main():
    test_case1()


if __name__ == "__main__":
    main()
