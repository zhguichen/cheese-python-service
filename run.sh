#!/bin/bash

# AI Practice Service 启动脚本

# 进入项目目录
cd "$(dirname "$0")"

# 确保 uv 可用
if ! command -v uv >/dev/null 2>&1; then
  echo "uv 未安装，请先安装 uv 后再运行此脚本。"
  exit 1
fi

# 使用 uv 执行应用
# 启动服务
echo "Starting AI Practice Service..."
uv run --python 3.11 python -m app.main
