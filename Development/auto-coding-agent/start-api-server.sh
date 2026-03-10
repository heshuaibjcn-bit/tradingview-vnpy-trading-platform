#!/bin/bash

# StockAutoTrader - Python API Server启动脚本
# Start script for Python API Server

set -e

# 脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR/trading-core"

echo "🚀 Starting StockAutoTrader Python API Server..."
echo "📁 Working directory: $(pwd)"

# 激活虚拟环境
if [ -d "venv" ]; then
    echo "✅ Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found!"
    echo "Please run: cd trading-core && python -m venv venv"
    exit 1
fi

# 检查依赖
echo "📦 Checking dependencies..."
pip install -q -r requirements.txt

# 启动API服务器
echo ""
echo "🔥 Starting API Server on http://127.0.0.1:8000"
echo "📚 API Documentation: http://127.0.0.1:8000/docs"
echo ""
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn api_server:app \
    --host 127.0.0.1 \
    --port 8000 \
    --reload \
    --log-level info
