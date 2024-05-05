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



def main():
    tasks = [Task1(), Task2(), Task3(), Task4()]
    p = tasksflow.pool.Pool(tasks)
    result = p.run()
    print(f"result: {result}")


if __name__ == "__main__":
    main()
