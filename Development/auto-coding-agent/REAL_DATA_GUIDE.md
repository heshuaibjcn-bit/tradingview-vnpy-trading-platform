# 接入真实市场数据指南

## 概述

本项目已成功接入真实市场数据，支持从**东方财富**和**新浪财经**获取实时行情数据。

## 架构说明

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│  Next.js    │────────▶│  Python API  │────────▶│ 东方财富API  │
│  Frontend   │◀────────│   Server     │◀────────│             │
└─────────────┘         └──────────────┘         └─────────────┘
                              │
                              ▼
                       ┌──────────────┐
                       │   新浪财经API  │
                       └──────────────┘
```

## 快速开始

### 1. 启动Python API服务器

```bash
# 方法1: 使用启动脚本（推荐）
./start-api-server.sh

# 方法2: 手动启动
cd trading-core
source venv/bin/activate
python api_server.py
```

服务器将在 `http://127.0.0.1:8000` 启动。

### 2. 启动Next.js前端

```bash
cd hello-nextjs
npm run dev
```

前端将在 `http://localhost:3000` 启动。

### 3. 验证连接

访问以下URL验证API是否正常：

- **API文档**: http://127.0.0.1:8000/docs
- **健康检查**: http://127.0.0.1:8000/health
- **数据源信息**: http://127.0.0.1:8000/api/sources

## API端点说明

### Python API服务器端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 根路径，返回服务信息 |
| `/health` | GET | 健康检查 |
| `/api/quote` | GET | 获取单个股票实时行情 |
| `/api/kline` | GET | 获取K线数据 |
| `/api/quotes/batch` | GET | 批量获取股票行情 |
| `/api/sources` | GET | 获取可用数据源 |

### 参数说明

#### `/api/quote` 参数

- `symbol` (必填): 股票代码，如 "600000"（浦发银行）、"000001"（平安银行）

**示例请求**:
```
GET http://127.0.0.1:8000/api/quote?symbol=600000
```

**响应示例**:
```json
{
  "symbol": "600000",
  "name": "浦发银行",
  "price": 10.52,
  "change": 0.12,
  "change_percent": 1.15,
  "open": 10.45,
  "high": 10.58,
  "low": 10.40,
  "volume": 1520000,
  "amount": 16050.5,
  "bid_price": 10.51,
  "ask_price": 10.52,
  "timestamp": "2026-03-10T14:30:00"
}
```

#### `/api/kline` 参数

- `symbol` (必填): 股票代码
- `period` (可选): 周期代码
  - `101` - 日K线（默认）
  - `102` - 周K线
  - `103` - 月K线
  - `5` - 1分钟K线
  - `15` - 5分钟K线
  - `30` - 30分钟K线
  - `60` - 60分钟K线
- `count` (可选): 数据条数，默认100，最大1000

**示例请求**:
```
GET http://127.0.0.1:8000/api/kline?symbol=600000&period=101&count=30
```

**响应示例**:
```json
{
  "symbol": "600000",
  "period": "101",
  "data": [
    {
      "timestamp": "2026-02-01T00:00:00",
      "open": 10.30,
      "high": 10.50,
      "low": 10.25,
      "close": 10.45,
      "volume": 1500000,
      "amount": 15750.0
    },
    ...
  ]
}
```

#### `/api/quotes/batch` 参数

- `symbols` (必填): 逗号分隔的股票代码

**示例请求**:
```
GET http://127.0.0.1:8000/api/quotes/batch?symbols=600000,000001,000002
```

## 前端调用示例

### Next.js API路由

前端通过以下路由调用Python后端：

```typescript
// 获取实时行情
GET /api/market/quote?symbol=600000

// 获取K线数据
GET /api/market/kline?symbol=600000&period=101&count=30
```

### React组件示例

```typescript
async function fetchQuote(symbol: string) {
  const response = await fetch(`/api/market/quote?symbol=${symbol}`);
  const data = await response.json();
  return data;
}
```

## 配置说明

### 环境变量

在 `hello-nextjs/.env.local` 中配置：

```bash
# Python API服务器地址
PYTHON_API_URL=http://127.0.0.1:8000
```

### 数据源配置

Python后端默认配置：
- **主数据源**: 东方财富
- **备用数据源**: 新浪财经

如需修改，编辑 `trading-core/market/fetcher.py`：

```python
fetcher = MarketDataFetcher(
    primary_source=MarketDataSource.EASTMONEY,  # 或 MarketDataSource.SINA
    fallback_sources=[MarketDataSource.SINA]
)
```

## 支持的股票代码

- **上海证券交易所**: 6xxxxx（如 600000 浦发银行）
- **深圳证券交易所**:
  - 0xxxxx（主板，如 000001 平安银行）
  - 3xxxxx（创业板，如 300001 特锐德）

## 常见问题

### 1. API服务器无法启动

**问题**: 端口8000已被占用

**解决**:
```bash
# 查找占用端口的进程
lsof -i :8000

# 杀死进程
kill -9 <PID>

# 或修改端口
# 编辑 api_server.py，将8000改为其他端口
```

### 2. 前端显示"Market data service unavailable"

**问题**: Python API服务器未启动

**解决**:
```bash
# 启动Python API服务器
./start-api-server.sh
```

### 3. 无法获取特定股票数据

**问题**: 股票代码不正确或数据源无数据

**解决**:
- 确认股票代码格式正确（6位数字）
- 访问 http://127.0.0.1:8000/docs 测试API
- 检查浏览器控制台和网络请求

### 4. 数据更新不及时

**问题**: 前端缓存了旧数据

**解决**:
- API已设置 `cache: "no-store"` 避免缓存
- 如仍有问题，清除浏览器缓存或硬刷新（Ctrl+Shift+R）

## 性能优化

### 数据缓存

Python后端实现了5秒的行情缓存：

```python
# trading-core/market/fetcher.py
self._cache_ttl = timedelta(seconds=5)  # 缓存5秒
```

### 批量查询

对于多个股票，使用批量接口：

```typescript
// 不推荐：多次请求
for (const symbol of symbols) {
  await fetch(`/api/market/quote?symbol=${symbol}`);
}

// 推荐：批量请求
await fetch(`/api/quotes/batch?symbols=${symbols.join(',')}`);
```

## 技术栈

- **Python后端**:
  - FastAPI: 高性能异步Web框架
  - Uvicorn: ASGI服务器
  - httpx: 异步HTTP客户端
  - Pydantic: 数据验证

- **前端**:
  - Next.js: React框架
  - TypeScript: 类型安全

## 下一步

1. **测试功能**: 在交易时段测试真实数据获取
2. **监控性能**: 观察API响应时间
3. **扩展功能**:
   - 添加更多技术指标
   - 实现WebSocket实时推送
   - 添加指数和板块数据

## 安全提醒

⚠️ **重要提示**:
- 本项目仅供学习和研究使用
- 真实交易存在风险，请谨慎操作
- 建议先在模拟环境充分测试
- 数据延迟可能影响交易决策

## 联系方式

如有问题，请查看：
- 项目文档: `/Development/auto-coding-agent/CLAUDE.md`
- 测试报告: `/Development/auto-coding-agent/TEST_REPORT.md`
- API文档: http://127.0.0.1:8000/docs（服务器运行时）
