#!/usr/bin/env python3

import tomllib
from pathlib import Path
import subprocess


def main():
    dir_project = Path(__file__).parent.parent

    def parse_version_from_pyproject(text: str) -> str:
        return tomllib.loads(text)["project"]["version"]

    def get_pyproject(branch: str) -> str:
        return subprocess.run(
            ["git", "show", f"{branch}:pyproject.toml"],
            capture_output=True,
            text=True,
            check=True,
            cwd=dir_project,
        ).stdout

    dev_version = parse_version_from_pyproject(get_pyproject("dev"))
    master_version = parse_version_from_pyproject(get_pyproject("master"))

    if dev_version == master_version:
        print("Dev and master versions are the same")
        exit(1)

    # git checkout master
    subprocess.run(["git", "checkout", "master"], cwd=dir_project, check=True)

    # git merge dev -m "merge dev"
    subprocess.run(
        ["git", "merge", "dev", "-m", "merge dev"], cwd=dir_project, check=True
    )

    # git push
    subprocess.run(["git", "push"], cwd=dir_project, check=True)

    # git checkout dev
    subprocess.run(["git", "checkout", "dev"], cwd=dir_project, check=True)


if __name__ == "__main__":
    main()
