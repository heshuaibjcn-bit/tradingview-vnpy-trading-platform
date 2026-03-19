# Agent开发指南

本指南介绍如何创建和实现自定义Agent。

## Agent基础

### Agent生命周期

每个Agent都有明确的生命周期：

```
INITIALIZED → STARTING → RUNNING → STOPPING → STOPPED
```

### 创建Agent

所有Agent必须继承`BaseAgent`并实现三个抽象方法：

```python
from agents.base import BaseAgent
from agents.messages import MessageType, AgentMessage

class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="my_agent",           # 唯一名称
            version="1.0.0",           # 版本
            description="我的Agent",    # 描述
            dependencies=[]            # 依赖的其他Agent
        )

    async def on_start(self):
        """Agent启动时调用"""
        # 订阅感兴趣的消息类型
        self.subscribe(MessageType.SOME_MESSAGE)

        # 初始化资源
        # 启动后台任务等

    async def on_stop(self):
        """Agent停止时调用"""
        # 清理资源
        # 停止后台任务等

    async def on_message(self, message: AgentMessage):
        """每条消息都会调用"""
        # 如果没有特定处理器，在这里处理
        pass
```

### 注册消息处理器

为特定消息类型注册处理器：

```python
class MyAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="my_agent", version="1.0.0")

        # 注册处理器
        self.register_handler(
            MessageType.MARKET_DATA_UPDATE,
            self._on_market_data
        )

    async def _on_market_data(self, message: AgentMessage):
        """处理市场数据更新"""
        symbol = message.content["symbol"]
        price = message.content["price"]

        # 处理数据...
        logger.info(f"Received {symbol} price: {price}")
```

### 发送消息

#### 广播消息（发送给所有订阅者）

```python
await self.send_message(
    MessageType.MY_EVENT,
    {"data": "value"}
)
```

#### 点对点消息（发送给特定Agent）

```python
await self.send_message(
    MessageType.MY_REQUEST,
    {"data": "value"},
    recipient="specific_agent"
)
```

#### 请求-响应模式

```python
# 发送请求
await self.send_message(
    MessageType.MY_REQUEST,
    {"query": "data"},
    recipient="data_agent",
    correlation_id="req_123"
)

# 在处理器中响应
async def _on_request(self, message: AgentMessage):
    # 处理请求...

    # 发送响应
    response = message.reply(
        {"result": "response_data"},
        sender=self.name
    )
    await self.send_message(
        response.msg_type,
        response.content,
        recipient=message.sender
    )
```

## 实际示例

### 示例1：数据源Agent

获取外部数据并广播：

```python
class DataSourceAgent(BaseAgent):
    def __init__(self, fetcher):
        super().__init__(
            name="data_source",
            version="1.0.0",
            description="获取外部数据"
        )
        self.fetcher = fetcher
        self._update_task = None

    async def on_start(self):
        # 启动后台更新任务
        self._update_task = asyncio.create_task(
            self._update_loop()
        )

    async def on_stop(self):
        if self._update_task:
            self._update_task.cancel()

    async def _update_loop(self):
        """定期获取数据"""
        while True:
            # 获取数据
            data = await self.fetcher.get_data()

            # 广播
            await self.send_message(
                MessageType.DATA_UPDATE,
                {"data": data}
            )

            # 等待下次更新
            await asyncio.sleep(5)
```

### 示例2：策略Agent

接收数据并生成信号：

```python
from agents.strategy_agent import StrategyAgent

class MyStrategyAgent(StrategyAgent):
    def __init__(self, strategy_engine):
        super().__init__(
            strategy_engine=strategy_engine,
            market_data_agent="market_fetcher"
        )

        # 添加自定义消息处理
        self.register_handler(
            MessageType.CUSTOM_INDICATOR,
            self._on_custom_indicator
        )

    async def _on_custom_indicator(self, message: AgentMessage):
        """处理自定义指标"""
        indicator_value = message.content["value"]

        # 根据指标生成信号
        if indicator_value > threshold:
            await self.send_message(
                MessageType.SIGNAL_GENERATED,
                {
                    "symbol": message.content["symbol"],
                    "signal_type": "buy",
                    "price": message.content["price"],
                    "strategy_name": "my_strategy",
                }
            )
```

### 示例3：通知Agent

发送通知到外部系统：

```python
class NotificationAgent(BaseAgent):
    def __init__(self, webhook_url: str):
        super().__init__(
            name="notification",
            version="1.0.0",
            description="发送通知"
        )
        self.webhook_url = webhook_url

        # 订阅所有告警
        self.subscribe(MessageType.ALERT_TRIGGERED)
        self.subscribe(MessageType.ORDER_FILLED)
        self.subscribe(MessageType.ERROR)

    async def on_start(self):
        """启动时验证连接"""
        await self._test_webhook()

    async def on_stop(self):
        pass

    async def on_message(self, message: AgentMessage):
        """处理需要通知的消息"""
        if message.msg_type in [
            MessageType.ALERT_TRIGGERED,
            MessageType.ORDER_FILLED,
            MessageType.ERROR,
        ]:
            await self._send_notification(message)

    async def _send_notification(self, message: AgentMessage):
        """发送通知"""
        import httpx

        payload = {
            "type": message.msg_type,
            "sender": message.sender,
            "content": message.content,
            "timestamp": message.timestamp.isoformat()
        }

        async with httpx.AsyncClient() as client:
            await client.post(
                self.webhook_url,
                json=payload
            )
```

## 最佳实践

### 1. 错误处理

始终处理异常并记录日志：

```python
async def on_message(self, message: AgentMessage):
    try:
        # 处理消息
        await self._process_message(message)
    except Exception as e:
        from loguru import logger
        logger.error(f"{self.name}: Error processing message - {e}")

        # 更新错误计数
        self._metrics.errors += 1
```

### 2. 异步操作

使用asyncio进行异步操作：

```python
async def on_start(self):
    # 并发初始化多个资源
    await asyncio.gather(
        self._connect_database(),
        self._connect_api(),
        self._load_config()
    )

async def _connect_database(self):
    # 连接数据库
    pass
```

### 3. 资源清理

在`on_stop`中正确清理资源：

```python
async def on_stop(self):
    # 停止后台任务
    if self._task:
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass

    # 关闭连接
    if self._client:
        await self._client.aclose()

    # 保存状态
    await self._save_state()
```

### 4. 健康检查

实现健康检查接口：

```python
async def health_check(self) -> bool:
    """检查Agent健康状态"""
    # 检查关键组件
    if not self._client or not self._database:
        return False

    # 检查最近活动
    if self._metrics.last_activity:
        idle_time = datetime.now() - self._metrics.last_activity
        if idle_time > timedelta(minutes=5):
            return False

    return True
```

### 5. 配置管理

使用配置初始化Agent：

```python
from pydantic import BaseSettings

class MyAgentConfig(BaseSettings):
    update_interval: float = 5.0
    max_retries: int = 3
    timeout: float = 30.0

    class Config:
        env_prefix = "MY_AGENT_"

class MyAgent(BaseAgent):
    def __init__(self, config: MyAgentConfig):
        super().__init__(
            name="my_agent",
            version="1.0.0"
        )
        self.config = config

    async def on_start(self):
        # 使用配置
        await self._start_with_interval(
            self.config.update_interval
        )
```

## 调试技巧

### 1. 消息追踪

使用correlation_id追踪消息流：

```python
# 发送带correlation_id的消息
correlation_id = f"req_{uuid.uuid4()}"

await self.send_message(
    MessageType.REQUEST,
    {"query": "data"},
    recipient="data_agent",
    correlation_id=correlation_id
)

# 记录correlation_id
logger.info(f"Sent request: {correlation_id}")
```

### 2. 消息历史

查看Agent收到的消息：

```python
# 获取最近的消息
history = self.get_message_history(limit=20)

for msg in history:
    print(f"{msg.timestamp} - {msg.msg_type}")
```

### 3. 指标监控

检查Agent指标：

```python
# 获取指标
metrics = self.metrics

print(f"Messages sent: {metrics.messages_sent}")
print(f"Messages received: {metrics.messages_received}")
print(f"Errors: {metrics.errors}")
print(f"Uptime: {metrics.uptime_seconds}s")
```

### 4. 状态查询

查询Agent状态：

```python
# 获取完整信息
info = self.get_info()

print(f"Status: {info.status}")
print(f"Health: {info.health}")
print(f"Uptime: {info.uptime}")
```

## 测试Agent

### 单元测试

```python
import pytest

def test_agent_initialization():
    agent = MyAgent()
    assert agent.name == "my_agent"
    assert agent.status == AgentStatus.INITIALIZED

@pytest.mark.asyncio
async def test_agent_lifecycle():
    agent = MyAgent()
    await agent.start()
    assert agent.status == AgentStatus.RUNNING

    await agent.stop()
    assert agent.status == AgentStatus.STOPPED
```

### 集成测试

```python
@pytest.mark.asyncio
async def test_agent_communication():
    from agents import TradingAgency

    agency = TradingAgency(enable_persistence=False)
    agency.register_agent(MyAgent())

    await agency.start()

    try:
        # 发送测试消息
        await agency.send_to_agent(
            "my_agent",
            MessageType.TEST,
            {"test": "data"}
        )

        await asyncio.sleep(0.1)

        # 验证
        # ...
    finally:
        await agency.stop()
```

## 常见问题

### Q: Agent启动失败

A: 检查依赖是否满足，查看日志中的错误堆栈。

### Q: 消息未送达

A: 确认已订阅消息类型，检查消息总线连接。

### Q: 性能问题

A: 使用批量处理，减少消息频率，优化处理器逻辑。

### Q: 内存泄漏

A: 确保在`on_stop`中清理所有资源，取消后台任务。

## 进阶主题

### 动态订阅

运行时改变订阅：

```python
async def on_message(self, message: AgentMessage):
    # 根据内容动态订阅
    if message.content.get("subscribe"):
        self.subscribe(MessageType.NEW_TYPE)
```

### 后台任务

启动长期运行的任务：

```python
async def on_start(self):
    self._task = asyncio.create_task(
        self._background_loop()
    )

async def _background_loop(self):
    while self.is_running:
        # 执行任务
        await self._do_work()
        await asyncio.sleep(1)
```

### 状态机

实现复杂状态逻辑：

```python
class StateMachineAgent(BaseAgent):
    def __init__(self):
        super().__init__(name="state_agent", version="1.0.0")
        self.state = "IDLE"

    async def on_message(self, message: AgentMessage):
        if self.state == "IDLE":
            if message.msg_type == MessageType.START:
                self.state = "RUNNING"
                # ...
        elif self.state == "RUNNING":
            if message.msg_type == MessageType.STOP:
                self.state = "IDLE"
                # ...
```

## 参考资源

- [架构文档](ARCHITECTURE.md)
- [BaseAgent API](../agents/base.py)
- [消息类型](../agents/messages.py)
- [示例Agent](../agents/)
