# Development & Contribution

## Environment Setup

Run the local development environment using `docker-compose`:

```sh
docker compose up -d
```

Install Docker and Remote Container plugins in VSCode, then click on the Docker Tab. Once the status of the `tasksflow-dev` container changes from `starting` to `running`, select the `tasksflow-dev` container, click on `Attach Visual Studio Code`, and open the `/workspace` folder inside the container.

## Common Commands

```sh
rye test # Run tests
rye test -- --cov # Run tests and print test coverage
rye test -- -s # Run tests and print logs
rye test -- -s ./tests/cache_test.py::test_cache_work # Run a specific test and print logs
rye build # Build wheel package
mypy --python-executable .venv/bin/python --exclude docs . # Check with mypy
/workspace/.venv/bin/ruff check --fix # Check and auto-fix code with ruff
/workspace/.venv/bin/ruff format # Format code with ruff
/workspace/.venv/bin/python /workspace/scripts/release.py # Release a new version
```

## Contribution

The Git branch management strategy for this project is as follows: the `master` branch represents stable versions, with each commit corresponding to a release version. The `dev` branch serves as the development branch, where development takes place and is later merged into the `master` branch.

If you wish to contribute to this project, please follow these steps:

1. Fork this project.

2. Find the latest commit merged into `master` branch on the `dev` branch, and create a new branch from this commit for development.

3. Once development is complete, submit a PR to the `dev` branch.
