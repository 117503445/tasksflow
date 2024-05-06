# 开发

使用 `docker-compose` 运行本地开发环境：

```sh
docker compose up -d
```

VSCode 安装 Docker 和 Remote Container 插件，点击 Docker Tab。等待 `tasksflow-dev` 容器状态由 `starting` 变为 `running` 后，选中 `tasksflow-dev` 容器，点击 `Attach Visual Studio Code / 附加 VSCode`，并打开容器内的 `/workspace` 文件夹。

以下是常用命令

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
