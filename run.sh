#!/bin/bash

# AI Practice Service 启动脚本

# 激活 conda 环境
source $(conda info --base)/etc/profile.d/conda.sh
conda activate cheese

# 进入项目目录
cd "$(dirname "$0")"

# 启动服务
echo "Starting AI Practice Service..."
python -m app.main

