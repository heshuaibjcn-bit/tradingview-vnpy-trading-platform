#!/bin/bash

# Agent Monitoring Dashboard启动脚本

echo "🚀 Starting Trading System Agent Monitoring Dashboard..."
echo ""

# 检查系统是否运行
if ! pgrep -f "python.*main.py" > /dev/null; then
    echo "⚠️  Warning: Trading system is not running!"
    echo "   Starting the system first..."
    cd "$(dirname "$0")"
    ./venv/bin/python main.py &
    sleep 3
    echo ""
fi

# 进入dashboard目录
cd "$(dirname "$0")/dashboard"

# 检查端口8080是否被占用
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "⚠️  Port 8080 is already in use"
    echo "   Trying to use port 8081..."
    PORT=8081
else
    PORT=8080
fi

echo "✅ Dashboard will be available at: http://localhost:$PORT"
echo ""
echo "Press Ctrl+C to stop the dashboard server"
echo ""

# 启动HTTP服务器
python3 -m http.server $PORT
