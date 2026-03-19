# 部署和运维指南

## 快速启动
\`\`\`bash
# 安装依赖
pip install -r requirements.txt

# 启动系统
python main.py
\`\`\`

## Docker部署
\`\`\`bash
docker build -t trading-system .
docker run -p 8000:8000 -p 8765:8765 trading-system
\`\`\`

## 监控
- 健康检查: http://localhost:8000/health
- 性能监控: http://localhost:8000/api/performance/status
- Agent状态: http://localhost:8000/api/agents
