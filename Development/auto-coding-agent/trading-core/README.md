# StockAutoTrader - Python Trading Core

股票全自动交易软件的核心交易模块（Python）。

## 功能模块

### 核心模块
- **automation/** - 同花顺自动化交易模块
  - 窗口识别和定位
  - 自动登录、买入、卖出、撤单
  - 模板匹配 UI 元素识别

- **strategies/** - 策略引擎和预设策略
  - 策略基类 (BaseStrategy)
  - MA 均线策略
  - MACD 指标策略
  - KDJ 随机指标策略
  - 突破策略
  - 网格交易策略

- **market/** - 行情数据获取和处理
  - 东方财富 API
  - 新浪财经 API
  - 技术指标计算器 (SMA, EMA, MACD, KDJ, RSI)
  - 行情数据缓存

- **websocket/** - WebSocket 服务器
  - 实时行情推送
  - 交易状态推送
  - 策略信号推送

- **risk/** - 风险控制系统
  - 仓位限制
  - 交易限制（日内次数、亏损限额）
  - 止损止盈管理
  - 风险检查器

- **security/** - 安全模块
  - 交易密码验证
  - 权限管理
  - 策略沙箱（模拟交易）
  - 审计日志

- **backtesting/** - 回测系统
  - 历史数据获取
  - 回测引擎
  - 性能指标计算

- **monitoring/** - 系统监控
  - 健康检查
  - 自动恢复
  - 日志缓冲

- **alerts/** - 告警系统
  - 价格告警
  - 成交量告警
  - 指标告警

- **trade_log/** - 交易日志
  - 交易记录
  - 信号记录
  - 性能分析

## 环境配置

1. 复制 `.env.example` 到 `.env`
2. 填写配置信息

```bash
cp .env.example .env
```

### 环境变量说明

```env
# 同花顺配置
THS_WINDOW_TITLE=同花顺

# Supabase 配置
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# 行情数据 API
EASTMONEY_ENABLED=true
SINA_ENABLED=true

# WebSocket 配置
WS_HOST=127.0.0.1
WS_PORT=8765

# 日志配置
LOG_LEVEL=INFO
```

## 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 测试

```bash
# 运行所有测试
pytest tests/

# 运行特定测试文件
pytest tests/test_strategies.py

# 查看测试覆盖率
pytest --cov=. tests/
```

## 依赖说明

### GUI 自动化
- `pyautogui` - 鼠标键盘自动化
- `pywin32` - Windows API (仅 Windows)
- `opencv-python` - 图像处理和模板匹配
- `pytesseract` - OCR 文字识别

### 数据处理
- `pandas` - 数据分析
- `numpy` - 数值计算

### 网络通信
- `websockets` - WebSocket 服务器
- `aiohttp` - 异步 HTTP 客户端
- `requests` - 同步 HTTP 客户端

### 数据库
- `supabase` - Supabase 客户端
- `asyncpg` - 异步 PostgreSQL 驱动

### 日志和配置
- `loguru` - 日志系统
- `python-dotenv` - 环境变量管理
- `pydantic` - 数据验证

### 测试
- `pytest` - 测试框架
- `pytest-asyncio` - 异步测试支持

## 模块使用示例

### 使用策略引擎

```python
from strategies.engine import StrategyEngine
from strategies.ma_strategy import create_ma_strategy

# 创建策略引擎
engine = StrategyEngine()

# 创建并添加策略
ma_strategy = create_ma_strategy({
    "name": "MA策略",
    "symbols": ["600000", "000001"],
    "short_period": 5,
    "long_period": 20,
})

engine.add_strategy(ma_strategy)

# 启动策略
await engine.start()
```

### 使用行情数据

```python
from market.fetcher import get_market_data

# 获取实时行情
quote = await get_market_data("600000")
print(f"价格: {quote.price}, 涨跌: {quote.change}%")

# 获取 K 线数据
kline = await get_market_data("600000", period="daily", count=100)
```

### 使用风险控制

```python
from risk.manager import RiskManager

# 创建风险管理器
risk_mgr = RiskManager()

# 设置风险限制
risk_mgr.set_daily_loss_limit(5000)
risk_mgr.set_max_position_size(10000)

# 预交易检查
result = risk_mgr.pre_trade_check(
    user_id="user1",
    symbol="600000",
    side="BUY",
    quantity=1000,
    price=10.50
)

if result.allowed:
    print("交易允许")
else:
    print(f"交易被拒绝: {result.reason}")
```

### 使用回测系统

```python
from backtesting.engine import BacktestEngine

# 创建回测引擎
engine = BacktestEngine(initial_capital=100000)

# 加载历史数据
await engine.load_data("600000", start_date="2023-01-01", end_date="2023-12-31")

# 运行回测
result = await engine.run(strategy)

print(f"收益率: {result.total_return:.2%}")
print(f"夏普比率: {result.sharpe_ratio:.2f}")
```

## 架构说明

### 异步架构
所有 I/O 操作（网络、数据库）都使用 async/await 模式，确保高并发性能。

### 策略接口
所有策略继承 `BaseStrategy`，实现 `generate_signals()` 方法：

```python
async def generate_signals(self) -> List[Signal]:
    # 获取市场数据
    market_data = await self._get_market_data()

    # 计算指标
    indicators = self._calculate_indicators(market_data)

    # 生成信号
    signals = self._generate_signals_from_indicators(indicators)

    return signals
```

### 信号格式
```python
{
    "symbol": "600000",
    "signal_type": "BUY",  # BUY, SELL, HOLD
    "price": 10.50,
    "quantity": 1000,
    "confidence": 0.85,
    "reason": "金叉信号"
}
```

## 注意事项

1. **同花顺窗口**: 确保同花顺客户端已启动且窗口可见
2. **交易时间**: 只在交易时间段执行交易
3. **网络连接**: 需要稳定的网络连接获取行情
4. **风险控制**: 建议先在模拟环境测试策略

## 免责声明

本软件仅供学习和研究使用，不构成任何投资建议。
使用本软件进行实盘交易的所有风险由用户自行承担。
