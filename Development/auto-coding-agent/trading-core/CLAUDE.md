# Trading System v2.0 - Auto-Coding Instructions

## Project Overview

**项目名称**: StockAutoTrader v2.0
**阶段**: 优化与增强 (Phase 2)
**当前状态**: 基础架构已完成(Phase 1完成,所有任务1-20已完成)
**开始日期**: 2026-03-19

---

## MANDATORY: Auto-Coding Workflow

每个Agent会话必须遵循以下工作流程:

### Step 1: 环境检查

```bash
cd /Users/shuai/Development/auto-coding-agent/trading-core

# 检查虚拟环境
source venv/bin/activate  # 或 ./venv/bin/python

# 检查系统状态
ps aux | grep "python.*main.py"

# 如果需要启动系统
./venv/bin/python main.py
```

### Step 2: 选择下一个任务

读取 `task.json` 并选择一个任务:

选择标准(按优先级):
1. 选择 `passes: false` 的任务
2. 考虑依赖关系 - 基础功能优先
3. 选择最高优先级的不完整任务

**重要**: 一次只处理一个任务,专注完成。

### Step 3: 实现任务

- 仔细阅读任务描述和步骤
- 按照步骤实现所有功能
- 遵循现有代码模式和约定
- 参考已有的架构文档

### Step 4: 测试验证

实现后,验证所有步骤:

**测试要求:**

1. **代码修改**:
   - 运行 `pytest tests/ -v` 确保测试通过
   - 检查Python语法: `python -m py_compile <files>`
   - 验证系统运行正常

2. **功能验证**:
   - 测试新实现的API端点
   - 验证WebSocket消息流
   - 检查Agent状态
   - 查看日志无错误

3. **性能验证**:
   - 如果是性能优化任务,运行基准测试
   - 对比优化前后的性能指标

**测试清单:**
- [ ] 代码没有语法错误
- [ ] 现有测试通过
- [ ] 新功能测试通过
- [ ] 系统运行稳定
- [ ] 日志无异常

### Step 5: 更新进度

在 `progress.txt` 中记录工作:

```
## [Date] - Task [id]: [title]

### What was done:
- [具体实现的更改]

### Files Modified:
- file1.py - [changes]
- file2.py - [changes]

### Testing:
- [如何测试的]

### Results:
- [测试结果]
- [性能对比(如适用)]

### Notes:
- [任何相关说明]
```

### Step 6: 提交更改

**重要**: 所有更改必须在同一个commit中提交,包括task.json更新!

流程:
1. 更新 `task.json`,将任务的 `passes` 从 `false` 改为 `true`
2. 更新 `progress.txt` 记录工作内容
3. 一次性提交所有更改:

```bash
git add .
git commit -m "Task [id]: [title] - completed"
```

**规则:**
- 只有在所有步骤都验证通过后才标记 `passes: true`
- 永远不要删除或修改任务描述
- 永远不要从列表中移除任务
- 一个task的所有内容必须在同一个commit中提交

---

## 项目结构

```
trading-core/
├── agents/              # Agent架构核心
│   ├── base.py         # BaseAgent基类
│   ├── agency.py       # TradingAgency主控制器
│   ├── message_bus.py  # 消息总线
│   └── ...
├── strategies/         # 交易策略
├── market/            # 市场数据
├── risk/              # 风险管理
├── alerts/            # 告警系统
├── automation/        # 自动化交易
├── backtesting/       # 回测系统
├── monitoring/        # 监控
├── security/          # 安全机制
├── trade_log/         # 交易日志
├── config/            # 配置
├── api/               # REST API
├── websocket/         # WebSocket服务器
├── tests/             # 测试
├── docs/              # 文档
├── main.py            # 主程序入口
├── task.json          # 任务定义
├── progress.txt       # 进度日志
├── SYSTEM_STATUS.md   # 系统状态文档
└── IMPLEMENTATION_SUMMARY.md  # 实施总结
```

---

## 命令参考

```bash
# 启动系统
./venv/bin/python main.py

# 运行测试
pytest tests/ -v
pytest tests/agents/ -v  # 只测试agents

# 检查Agent状态 (通过WebSocket)
python3 -c "
import asyncio, websockets, json
async def check():
    async with websockets.connect('ws://localhost:8765') as ws:
        await ws.recv()
        await ws.send(json.dumps({'type': 'get_agents'}))
        print(json.loads(await ws.recv()))
asyncio.run(check())
"

# 查看日志
tail -f logs/trading.log

# 查看消息数据库
sqlite3 data/messages.db "SELECT msg_type, COUNT(*) FROM messages GROUP BY msg_type"

# 停止系统
pkill -f "python.*main.py"
```

---

## 编码规范

- Python 3.14+ asyncio优先
- 类型提示 (type hints)
- Docstring文档
- 单一职责原则
- 消息驱动架构
- 完整的错误处理

---

## 关键规则

1. **一次一个任务** - 专注完成好一个任务
2. **测试优先** - 所有步骤必须通过验证
3. **记录进度** - 在progress.txt中详细记录
4. **一次提交** - 所有更改(代码、progress.txt、task.json)在同一commit
5. **不删除任务** - 只将 `passes: false` 改为 `true`
6. **参考文档** - 充分利用现有架构文档
7. **保持稳定** - 确保系统持续运行

---

## 可用的资源和文档

- **架构文档**: docs/ARCHITECTURE.md
- **Agent开发指南**: docs/AGENT_DEVELOPMENT.md
- **系统状态**: SYSTEM_STATUS.md
- **实施总结**: IMPLEMENTATION_SUMMARY.md
- **主README**: README.md

---

## Phase 2 重点关注

### 性能优化
- 消息批处理 (Task 27)
- 异步并发优化 (Task 28)
- 缓存优化 (Task 29)

### 可视化
- Agent监控仪表板 (Task 21)
- 性能监控系统 (Task 23)

### 高级功能
- 策略热加载 (Task 24)
- 配置热更新 (Task 25)
- 动态Agent注册 (Task 26)

### 测试增强
- 性能压力测试 (Task 30)
- 混沌测试 (Task 31)
- 自动化回归测试 (Task 32)

### 分布式支持
- 分布式Agent支持 (Task 33)

### 运维工具
- 日志系统增强 (Task 34)
- API文档自动生成 (Task 35)
- 部署和运维 (Task 36)

---

## 开始开发

现在,选择下一个任务开始开发吧! 🚀

```bash
# 1. 查看任务列表
cat task.json | jq '.tasks[] | select(.passes == false)'

# 2. 选择一个任务,开始实现
# ...

# 3. 测试验证
# ...

# 4. 提交更改
git add .
git commit -m "Task XX: [title] - completed"
```
