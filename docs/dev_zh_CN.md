# 开发 & 贡献

## 环境搭建

使用 `docker-compose` 运行本地开发环境：

```sh
docker compose up -d
```

VSCode 安装 Docker 和 Remote Container 插件，点击 Docker Tab。等待 `tasksflow-dev` 容器状态由 `starting` 变为 `running` 后，选中 `tasksflow-dev` 容器，点击 `Attach Visual Studio Code / 附加 VSCode`，并打开容器内的 `/workspace` 文件夹。

## 常用命令

```sh
rye test # 运行测试
rye test -- --cov # 运行测试并打印测试覆盖率
rye test -- -s # 运行测试并打印日志
rye test -- -s ./tests/cache_test.py::test_cache_work # 运行单独测试并打印日志
rye build # 构建 wheel 包
mypy --python-executable .venv/bin/python --exclude docs . # 使用 mypy 进行检查
/workspace/.venv/bin/ruff check --fix # 使用 ruff 进行代码检查并自动修复
/workspace/.venv/bin/ruff format # 使用 ruff 进行代码格式化
/workspace/.venv/bin/python /workspace/scripts/release.py # 发布新版本
```

## 贡献

本项目的 Git 分支管理策略为 `master` 分支为稳定版本，每个 commit 对应一个 release 版本。`dev` 分支为开发分支，在 `dev` 分支上进行开发，开发完成后合并到 `master` 分支。

如果你想为本项目贡献代码，请按照以下步骤进行：

1. Fork 本项目

2. 在 `dev` 分支上寻找到最新被合入 master 的 commit，在此 commit 上创建新的分支进行开发。

3. 开发完成后，提交 PR 到 `dev` 分支。
