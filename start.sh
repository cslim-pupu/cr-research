#!/bin/bash

# HTML源代码版权分析器启动脚本
# 作者: AI助手
# 用途: 快速启动Web应用

echo "正在启动HTML源代码版权分析器..."
echo "请确保已安装Python 3.7+"

# 检查Python版本
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3，请先安装Python"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "安装依赖包..."
pip install -r requirements.txt

# 启动应用
echo "启动Web应用..."
echo "应用将在以下地址运行:"
echo "  - http://localhost:8080"
echo "  - http://127.0.0.1:8080"
echo ""
echo "按 Ctrl+C 停止应用"
echo "==========================================="

python web_app.py