# Trading System Agent Architecture

## 概述

本文档描述了交易系统的Agent架构设计和实现细节。

## 架构设计

### 整体架构图

```
┌─────────────────────────────────────────────────────────────┐
│                     TradingAgency (Agency)                   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              AgentMessageBus (消息总线)               │   │
│  │  - 发布/订阅模式                                      │   │
│  │  - 点对点消息                                         │   │
│  │  - 消息持久化到数据库                                 │   │
│  │  - 消息追踪和历史查询                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │  Strategy  │  │    THS     │  │   Market   │           │
│  │   Agent    │  │  Trader    │  │  Fetcher   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐           │
│  │    Risk    │  │   System   │  │   Alert    │           │
│  │  Manager   │  │  Monitor   │  │   Engine   │           │
│  └────────────┘  └────────────┘  └────────────┘           │
│                                                              │
│  ┌────────────┐  ┌────────────┐                           │
│  │    Trade   │  │    Audit   │                           │
│  │  Recorder  │  │   Logger   │                           │
│  └────────────┘  └────────────┘                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           AgentRegistry (服务注册中心)                │   │
│  │  - Agent注册与发现                                     │   │
│  │  - 健康检查                                           │   │
│  │  - 生命周期管理                                       │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 核心组件

#### 1. BaseAgent (基类)

所有Agent的抽象基类，定义标准接口。

**状态转换：**
```
INITIALIZED → STARTING → RUNNING → STOPPING → STOPPED
                                    ↓
                                  ERROR
```

**核心方法：**
- `start()` - 启动Agent
- `stop()` - 停止Agent
- `send_message()` - 发送消息
- `receive_message()` - 接收消息
- `subscribe()` - 订阅消息类型
- `register_handler()` - 注册消息处理器

#### 2. AgentMessageBus (消息总线)

负责Agent间的消息路由和传递。

**功能：**
- 发布/订阅模式（一对多）
- 点对点消息（一对一）
- 消息持久化（SQLite）
- 消息过滤
- 消息历史追踪

**使用示例：**
```python
# 创建消息总线
bus = AgentMessageBus()

# 注册Agent
bus.register_agent(agent)

# 订阅消息
agent.subscribe(MessageType.MARKET_DATA_UPDATE)

# 发送消息
await bus.publish(message)
```

#### 3. AgentRegistry (注册中心)

管理Agent的注册、发现和健康检查。

**功能：**
- Agent注册与注销
- 30秒间隔健康检查
- 按依赖顺序启动/停止
- 自动检测ERROR状态Agent

#### 4. TradingAgency (主控制器)

系统主控制器，统一管理所有Agent。

**功能：**
- 生命周期管理
- 健康监控
- 消息广播
- 紧急停止

## 消息类型

### 市场数据
- `MARKET_DATA_UPDATE` - 市场数据更新
- `MARKET_DATA_REQUEST` - 请求数据
- `KLINE_REQUEST` - K线数据请求

### 交易信号
- `SIGNAL_GENERATED` - 信号生成
- `SIGNAL_EXECUTED` - 信号执行
- `SIGNAL_CANCELLED` - 信号取消

### 交易执行
- `ORDER_REQUEST` - 订单请求
- `ORDER_FILLED` - 订单成交
- `ORDER_FAILED` - 订单失败
- `ORDER_CANCELLED` - 订单取消

### 风险管理
- `RISK_CHECK_REQUEST` - 风险检查请求
- `RISK_CHECK_RESPONSE` - 风险检查响应
- `RISK_LIMIT_BREACHED` - 风险限制触发

### 策略管理
- `STRATEGY_START` - 启动策略
- `STRATEGY_STOP` - 停止策略
- `STRATEGY_UPDATE` - 更新策略

### 告警
- `ALERT_TRIGGERED` - 告警触发
- `ALERT_ACKNOWLEDGED` - 告警确认

### 监控
- `HEALTH_CHECK` - 健康检查
- `HEALTH_STATUS` - 健康状态

### 审计
- `AUDIT_LOG` - 审计日志

### 系统控制
- `SYSTEM_START` - 系统启动
- `SYSTEM_STOP` - 系统停止
- `EMERGENCY_STOP` - 紧急停止

## Agent封装

### StrategyAgent

封装StrategyEngine，负责策略执行和信号生成。

**职责：**
- 订阅MARKET_DATA_UPDATE
- 执行策略
- 生成SIGNAL_GENERATED消息
- 处理STRATEGY_START/STOP消息

### THSTraderAgent

封装THSTrader，负责订单执行。

**职责：**
- 处理ORDER_REQUEST
- 发送RISK_CHECK_REQUEST
- 执行订单（通过THSTrader）
- 发送ORDER_FILLED/ORDER_FAILED消息

**执行流程：**
```
1. 接收ORDER_REQUEST
2. 发送RISK_CHECK_REQUEST
3. 接收RISK_CHECK_RESPONSE
4. 如果通过 → 执行订单
5. 发送ORDER_FILLED
```

### MarketDataAgent

封装MarketDataFetcher，负责市场数据获取。

**职责：**
- 定期发布MARKET_DATA_UPDATE（1秒间隔）
- 处理MARKET_DATA_REQUEST
- 处理KLINE_REQUEST
- 缓存管理

### RiskManagerAgent

封装RiskManager，负责风险检查。

**职责：**
- 处理RISK_CHECK_REQUEST
- 执行风险检查
- 发送RISK_CHECK_RESPONSE
- 跟踪仓位和资金

### SystemMonitorAgent

封装SystemMonitor，负责系统健康监控。

**职责：**
- 定期发送HEALTH_STATUS
- 自动恢复支持
- 监控Agent状态

### AlertEngineAgent

封装AlertEngine，负责告警。

**职责：**
- 订阅MARKET_DATA_UPDATE
- 检查告警规则
- 发送ALERT_TRIGGERED

### TradeRecorderAgent

封装TradeRecorder/SignalRecorder，负责交易记录。

**职责：**
- 订阅ORDER_FILLED, SIGNAL_GENERATED
- 记录到日志和数据库

### AuditLoggerAgent

封装AuditLogger，负责审计日志。

**职责：**
- 订阅所有重要消息类型
- 记录审计事件

## 配置

在 `config/settings.py` 中配置：

```python
# Agent Architecture
USE_AGENT_ARCHITECTURE: bool = True  # 特性开关
AGENT_MESSAGE_DB_PATH: str = "data/messages.db"
AGENT_MESSAGE_RETENTION_DAYS: int = 30
AGENT_HEALTH_CHECK_INTERVAL: float = 30.0
AGENT_MESSAGE_HISTORY_SIZE: int = 1000
AGENT_ENABLE_PERSISTENCE: bool = True
```

## 使用示例

### 基本使用

```python
from agents import TradingAgency
from agents.strategy_agent import StrategyAgent
from agents.market_agent import MarketDataAgent
from strategies.engine import StrategyEngine
from market.fetcher import MarketDataFetcher

# 创建Agency
agency = TradingAgency()

# 初始化组件
strategy_engine = StrategyEngine()
market_fetcher = MarketDataFetcher()

# 注册Agent
agency.register_agent(StrategyAgent(strategy_engine))
agency.register_agent(MarketDataAgent(market_fetcher))

# 启动
await agency.start()

try:
    # 运行...
    await asyncio.sleep(3600)  # 运行1小时
finally:
    await agency.stop()
```

### 发送消息

```python
# 广播消息
await agency.broadcast_message(
    MessageType.HEALTH_CHECK,
    {"check_type": "full"}
)

# 发送给特定Agent
await agency.send_to_agent(
    "market_fetcher",
    MessageType.MARKET_DATA_REQUEST,
    {"symbols": ["000001"]}
)
```

### 查询状态

```python
# 获取系统状态
status = agency.get_status()
print(f"Running agents: {status['agents']['running']}")

# 获取健康状态
health = agency.get_health_summary()
print(f"Healthy agents: {health['healthy']}")

# 获取Agent详情
agent_info = agency.get_agent_status("strategy_engine")
print(f"Strategy status: {agent_info['status']}")
```

## API接口

### Agent管理API

- `GET /api/agents` - 列出所有Agent
- `GET /api/agents/{name}` - 获取Agent详情
- `POST /api/agents/{name}/start` - 启动Agent
- `POST /api/agents/{name}/stop` - 停止Agent
- `POST /api/agents/{name}/restart` - 重启Agent
- `GET /api/agents/status` - 获取系统状态
- `GET /api/agents/health` - 获取健康状态
- `POST /api/agents/emergency-stop` - 紧急停止

### 消息API

- `GET /api/agents/messages/history` - 查询消息历史
- `GET /api/agents/messages/conversation/{correlation_id}` - 获取对话历史
- `POST /api/agents/messages/broadcast` - 广播消息
- `POST /api/agents/messages/{agent_name}` - 发送消息给指定Agent

### 其他API

- `GET /api/agents/subscriptions` - 获取所有订阅
- `GET /api/agents/metrics` - 获取系统指标

## 数据持久化

### 消息数据库

SQLite数据库存储所有消息：

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    msg_type TEXT NOT NULL,
    sender TEXT NOT NULL,
    recipient TEXT,
    content_json TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    correlation_id TEXT,
    reply_to TEXT
)
```

### 查询示例

```python
from agents.database import MessageDatabase

db = MessageDatabase("data/messages.db")

# 获取最近100条消息
messages = db.get_messages(limit=100)

# 获取特定类型的消息
market_data = db.get_messages(
    msg_type="MARKET_DATA_UPDATE",
    limit=50
)

# 获取对话历史
conversation = db.get_conversation(correlation_id="...")
```

## 性能指标

目标性能指标：

- 消息吞吐量：≥1000消息/秒
- 消息延迟：≤10ms (P99)
- 内存使用：≤500MB（8个Agent运行）
- 启动时间：≤5秒

## 故障排查

### Agent无法启动

1. 检查依赖是否满足
2. 查看日志错误信息
3. 检查Agent状态

```python
status = agency.get_agent_status("agent_name")
print(status)
```

### 消息未送达

1. 检查订阅是否正确
2. 查看消息历史
3. 检查消息过滤器

```python
subscriptions = agency.message_bus.get_agent_subscriptions("agent_name")
print(subscriptions)

history = agency.message_bus.get_message_history(limit=10)
print(history)
```

### 健康检查失败

1. 查看健康摘要
2. 检查Agent错误计数
3. 查看Agent指标

```python
health = agency.get_health_summary()
print(health)

info = agency.get_agent_status("agent_name")
print(info['metrics'])
```

## 最佳实践

1. **消息设计**
   - 使用标准消息类型
   - 包含完整上下文信息
   - 使用correlation_id追踪请求

2. **Agent设计**
   - 保持单一职责
   - 异步处理
   - 错误处理和日志记录

3. **监控**
   - 定期检查健康状态
   - 监控消息吞吐量
   - 设置告警规则

4. **测试**
   - 单元测试每个Agent
   - 集成测试消息流
   - 端到端测试完整流程

## 迁移指南

### 从旧架构迁移

1. **启用Agent架构**
   ```python
   # config/settings.py
   USE_AGENT_ARCHITECTURE = True
   ```

2. **更新代码**
   - 旧的回调 → 消息处理器
   - 旧的直接调用 → 消息发送

3. **验证**
   - 运行测试
   - 检查日志
   - 监控性能

### 回滚

如果需要回滚到旧架构：

```python
USE_AGENT_ARCHITECTURE = False
```

## 扩展性

### 添加新Agent

1. 继承BaseAgent
2. 实现抽象方法
3. 注册到TradingAgency

```python
class MyAgent(BaseAgent):
    async def on_start(self):
        self.subscribe(MessageType.SOME_MESSAGE)

    async def on_stop(self):
        pass

    async def on_message(self, message):
        # 处理消息
        pass

# 注册
agency.register_agent(MyAgent())
```

### 添加新消息类型

1. 在messages.py中添加
2. 更新MESSAGE_SCHEMAS
3. 创建辅助函数

## 未来改进

1. **分布式支持** - 跨机器部署Agent
2. **消息队列升级** - Redis/RabbitMQ
3. **Agent可视化** - 监控仪表板
4. **策略热加载** - 运行时添加/删除策略
5. **配置热更新** - 运行时修改Agent配置

## 参考资料

- [FastAPI文档](https://fastapi.tiangolo.com/)
- [WebSocket文档](https://websockets.readthedocs.io/)
- [AsyncIO文档](https://docs.python.org/3/library/asyncio.html)
