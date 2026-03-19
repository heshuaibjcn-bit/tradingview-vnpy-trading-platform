# Agent Monitoring Dashboard

实时监控Trading System Agent状态和消息流的Web仪表板。

## 功能特性

- ✅ 实时Agent状态监控
- ✅ 消息流实时显示
- ✅ 性能指标图表(吞吐量、健康分布)
- ✅ Agent控制面板(启动/停止/重启)
- ✅ 消息历史查询和过滤
- ✅ Agent详情查看
- ✅ WebSocket实时数据推送
- ✅ 响应式设计,支持移动端

## 快速开始

### 1. 启动交易系统

```bash
cd /Users/shuai/Development/auto-coding-agent/trading-core
./venv/bin/python main.py
```

系统会自动启动:
- REST API服务器 (http://localhost:8000)
- WebSocket服务器 (ws://localhost:8765)

### 2. 打开监控仪表板

有两种方式打开仪表板:

**方式1: 直接打开HTML文件**
```bash
open dashboard/index.html
# 或者使用你喜欢的浏览器打开
```

**方式2: 使用Python HTTP服务器**
```bash
cd dashboard
python3 -m http.server 8080
# 然后访问 http://localhost:8080
```

### 3. 验证连接

打开仪表板后,你应该看到:
- 连接状态显示为"Connected"(绿色指示灯)
- Agent列表显示所有注册的Agent
- 消息流实时更新
- 性能图表正常显示

## 仪表板功能

### 系统概览
顶部显示4个关键指标:
- **Total Agents**: 总Agent数量
- **Running**: 正在运行的Agent数量
- **Healthy**: 健康的Agent数量
- **Uptime**: 系统运行时间

### Agent列表
- 显示所有Agent的实时状态
- 点击Agent卡片查看详细信息
- 显示消息数、错误数、运行时间

### Agent控制
在Agent详情弹窗中可以:
- **Start**: 启动已停止的Agent
- **Stop**: 停止正在运行的Agent
- **Restart**: 重启Agent

### 消息流
实时显示Agent间通信消息:
- 消息类型
- 发送者
- 时间戳
- 内容预览

### 性能图表

**Message Throughput**:
- 实时消息吞吐量(消息/秒)
- 最近20个数据点

**Agent Health Distribution**:
- 健康Agent占比
- 不健康Agent占比
- 未知状态Agent占比

### 消息历史
- 完整的消息历史记录
- 支持按类型过滤
- 支持关键字搜索
- 显示最近50条消息

## API端点

仪表板使用以下API端点:

| 端点 | 方法 | 描述 |
|------|------|------|
| `/api/agents` | GET | 获取所有Agent列表 |
| `/api/agents/{name}` | GET | 获取特定Agent详情 |
| `/api/agents/{name}/start` | POST | 启动Agent |
| `/api/agents/{name}/stop` | POST | 停止Agent |
| `/api/agents/{name}/restart` | POST | 重启Agent |
| `/api/agents/metrics` | GET | 获取系统指标 |
| `/api/agents/messages/history` | GET | 获取消息历史 |
| `/api/agents/health` | GET | 获取健康摘要 |

## WebSocket消息类型

客户端可以发送以下消息:

| 类型 | 描述 |
|------|------|
| `get_agents` | 获取Agent状态 |
| `get_health` | 获取健康摘要 |
| `ping` | 心跳检测 |

服务器会推送以下消息:

| 类型 | 描述 |
|------|------|
| `agent_status` | Agent状态更新 |
| `agent_health` | 健康状态更新 |
| `agent_message` | 新消息通知 |
| `pong` | 心跳响应 |

## 配置

可以在`dashboard.js`中修改配置:

```javascript
const CONFIG = {
    WS_URL: 'ws://localhost:8765',        // WebSocket地址
    API_URL: 'http://localhost:8000',      // API地址
    REFRESH_INTERVAL: 5000,                // 刷新间隔(毫秒)
    MAX_MESSAGES: 100,                     // 最大消息历史数
    CHART_HISTORY: 20                      // 图表历史数据点
};
```

## 故障排查

### 无法连接到WebSocket

**症状**: 连接状态显示"Disconnected"(红色)

**解决方案**:
1. 确认交易系统正在运行:
   ```bash
   ps aux | grep "python.*main.py"
   ```
2. 检查WebSocket端口(8765)是否被占用:
   ```bash
   lsof -i :8765
   ```
3. 查看系统日志:
   ```bash
   tail -f logs/trading.log
   ```

### Agent数据不显示

**症状**: 仪表板连接正常,但Agent列表为空

**解决方案**:
1. 检查Agent架构是否启用:
   ```python
   # 在config/settings.py中
   USE_AGENT_ARCHITECTURE = True
   ```
2. 检查API是否正常:
   ```bash
   curl http://localhost:8000/api/agents
   ```

### 消息流不更新

**症状**: 消息流显示"Waiting for messages..."

**解决方案**:
1. 确认Agent正在产生消息
2. 检查WebSocket消息订阅:
   - 系统会自动订阅所有Agent消息
   - 查看浏览器控制台是否有错误

## 技术栈

- **前端**: 原生JavaScript + HTML5
- **样式**: Tailwind CSS (CDN)
- **图表**: Chart.js
- **通信**: WebSocket + REST API
- **后端**: Python FastAPI + asyncio

## 浏览器兼容性

- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 性能建议

1. **消息历史限制**: 默认只显示最近50条消息,避免内存占用过高
2. **图表数据点**: 默认保留最近20个数据点
3. **自动刷新**: 每5秒刷新一次,可调整`REFRESH_INTERVAL`
4. **WebSocket优先**: 实时数据通过WebSocket推送,减少API轮询

## 后续改进

- [ ] 添加用户认证
- [ ] 支持多系统监控
- [ ] 添加告警通知
- [ ] 支持自定义仪表板布局
- [ ] 添加数据导出功能
- [ ] 支持暗色/亮色主题切换

## 维护

定期清理消息数据库:

```bash
# 查看数据库大小
ls -lh data/messages.db

# 清理30天前的消息
sqlite3 data/messages.db "DELETE FROM messages WHERE timestamp < datetime('now', '-30 days')"
```

## 支持

如有问题,请查看:
- 系统架构文档: `docs/ARCHITECTURE.md`
- Agent开发指南: `docs/AGENT_DEVELOPMENT.md`
- 系统状态: `SYSTEM_STATUS.md`
