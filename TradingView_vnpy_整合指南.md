# TradingView + vnpy 整合使用指南

## 🎯 项目概述

将 TradingView 的专业图表能力与 vnpy 的交易执行能力整合，打造专业级量化交易平台。

### 核心功能
- ✅ **TradingView 图表** - 专业级图表分析
- ✅ **vnpy 交易** - 强大的交易执行能力
- ✅ **东财接口** - A 股实盘交易
- ✅ **Webhook 自动化** - 警报自动转交易

---

## 📁 项目文件

### 核心组件
```
/Users/shuai/
├── tradingview_webhook_server.py      # Webhook 服务器
├── tradingview_vnpy_integrated.py     # 整合图形界面
├── vnpy_gateway_eastmoney.py          # 东财交易网关
└── start_vnpy.py                      # vnpy 启动脚本
```

---

## 🚀 快速开始

### 方式一：使用整合图形界面（推荐）

#### 1. 启动整合界面
```bash
cd /Users/shuai
source vnpy_env/bin/activate
python tradingview_vnpy_integrated.py
```

#### 2. 界面布局
```
┌─────────────────────────────────────────────────────────┐
│  TradingView + vnpy 专业量化终端                          │
├──────────────────────┬──────────────────────────────────┤
│                      │                                  │
│  TradingView 图表    │    vnpy 交易面板                 │
│  (70%)               │    (30%)                         │
│                      │                                  │
│  - 专业K线图         │  - 账户信息                      │
│  - 技术指标           │  - 快速下单                      │
│  - 画线工具           │  - 持仓列表                      │
│  - 警报管理           │  - 订单管理                      │
│                      │                                  │
├──────────────────────────────────────────────────────────┤
│  TradingView Webhook 日志                                │
│  [14:30:25] 系统启动成功                                  │
│  [14:30:26] TradingView 图表已加载                        │
└──────────────────────────────────────────────────────────┘
```

#### 3. 配置东财账号
- 在 vnpy 交易面板中点击"连接"
- 填入账号信息和 Cookie

---

### 方式二：独立运行 Webhook 服务器

#### 1. 启动 Webhook 服务器
```bash
cd /Users/shuai
source vnpy_env/bin/activate
python tradingview_webhook_server.py
```

#### 2. 服务器信息
```
地址: http://0.0.0.0:5000
Webhook: http://your-ip:5000/webhook
状态查询: http://your-ip:5000/status
```

---

## 🔗 配置 TradingView 警报

### 步骤 1：创建 TradingView 账号
1. 访问 https://www.tradingview.com
2. 注册账号（免费版即可）

### 步骤 2：设置图表警报
1. 打开任意股票图表（如 A 股）
2. 点击顶部"警报"按钮
3. 设置警报条件：
   - 价格突破
   - 技术指标信号
   - 画线工具触发

### 步骤 3：配置 Webhook

#### 警报消息设置：
```
{{ticker}}, {{close}}, {{interval}}
```

#### Webhook URL 设置：
```
http://your-server-ip:5000/webhook
```

#### 警报消息模板（JSON 格式）：
```json
{
  "symbol": "600000",
  "action": "buy",
  "price": {{close}},
  "volume": 100,
  "exchange": "SSE"
}
```

### 步骤 4：测试警报
```python
# 使用 curl 测试 Webhook
curl -X POST http://localhost:5000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "600000",
    "action": "buy",
    "price": 10.5,
    "volume": 100,
    "exchange": "SSE"
  }'
```

---

## 💡 使用场景

### 场景 1：技术指标自动交易
```
TradingView RSI 指标 → Webhook → vnpy 自动下单
```

**配置示例：**
1. TradingView 设置 RSI < 30 买入警报
2. Webhook 自动触发 vnpy 买入订单
3. RSI > 70 卖出警报自动平仓

### 场景 2：趋势跟踪策略
```
TradingView 画线工具 → 突破警报 → vnpy 追踪交易
```

**配置示例：**
1. 在图表上画趋势线
2. 价格突破趋势线触发警报
3. vnpy 自动执行趋势跟踪交易

### 场景 3：多周期共振
```
多个时间周期警报 → 综合判断 → vnpy 执行
```

**配置示例：**
1. 日线 + 周线同向突破
2. Webhook 服务器综合判断
3. 满足条件自动交易

---

## 🔧 高级配置

### 1. 自定义交易逻辑

编辑 `tradingview_webhook_server.py`：

```python
def process_alert(self, alert_data):
    """处理警报 - 自定义逻辑"""
    # 获取当前价格
    symbol = alert_data.get("symbol")
    tick = self.main_engine.get_tick(symbol)

    # 判断持仓
    positions = self.main_engine.get_all_positions()
    current_position = sum(p.volume for p in positions if p.symbol == symbol)

    # 自定义交易逻辑
    if alert_data.get("action") == "buy" and current_position == 0:
        # 无持仓时才买入
        return self.send_order(...)
    elif alert_data.get("action") == "sell" and current_position > 0:
        # 有持仓时才卖出
        return self.send_order(...)
```

### 2. 风险控制

添加止损止盈逻辑：

```python
# 在订单创建后设置止损止盈
def send_order_with_risk(self, order_req, stop_loss, take_profit):
    """带风险控制的下单"""
    # 发送主订单
    vt_orderid = self.main_engine.send_order(order_req, "EM")

    # 计算止损价
    if order_req.direction == Direction.LONG:
        stop_price = order_req.price * (1 - stop_loss)
        take_profit_price = order_req.price * (1 + take_profit)
    else:
        stop_price = order_req.price * (1 + stop_loss)
        take_profit_price = order_req.price * (1 - take_profit)

    # 创建止损止盈订单
    # ... (实现逻辑)

    return vt_orderid
```

### 3. 多策略管理

支持多个 TradingView 警报策略：

```python
strategies = {
    "strategy_1": {
        "symbol": "600000",
        "max_position": 1000,
        "risk_ratio": 0.02
    },
    "strategy_2": {
        "symbol": "000001",
        "max_position": 2000,
        "risk_ratio": 0.01
    }
}

def process_alert(self, alert_data):
    strategy_id = alert_data.get("strategy")
    strategy = strategies.get(strategy_id)

    if strategy:
        # 应用策略参数
        # ... (实现逻辑)
```

---

## 📊 监控与日志

### Webhook 服务器日志
```bash
# 查看服务器日志
tail -f /tmp/webhook_server.log
```

### vnpy 交易日志
- 在整合界面底部的日志窗口查看
- 或在 vnpy GUI 的日志窗口查看

### 状态监控
```bash
# 查询服务器状态
curl http://localhost:5000/status

# 返回示例
{
  "status": "running",
  "vnpy_connected": true,
  "accounts": 1,
  "positions": 2,
  "orders": 5,
  "gateway": "EM"
}
```

---

## 🔐 安全建议

### 1. 使用 HTTPS
```python
# 在生产环境使用 SSL 证书
app.run(host="0.0.0.0", port=443, ssl_context='adhoc')
```

### 2. 验证 Webhook 来源
```python
@app.route("/webhook", methods=["POST"])
def webhook():
    # 验证请求来源
    api_key = request.headers.get("X-API-Key")
    if api_key != YOUR_SECRET_KEY:
        return jsonify({"error": "Unauthorized"}), 401

    # 处理警报
    # ...
```

### 3. 限流保护
```python
from flask_limiter import Limiter

limiter = Limiter(app, key_func=lambda: request.remote_addr)

@app.route("/webhook", methods=["POST"])
@limiter.limit("10 per minute")
def webhook():
    # 限制每分钟最多 10 个请求
    # ...
```

---

## 🛠️ 故障排查

### 问题 1：TradingView 无法连接 Webhook
**原因**：网络不可达
**解决**：
- 检查服务器防火墙
- 使用 ngrok 等内网穿透工具
- 确认 Webhook URL 正确

### 问题 2：订单未执行
**原因**：vnpy 网关未连接
**解决**：
- 检查东财账号配置
- 确认 Cookie 未过期
- 查看网关连接日志

### 问题 3：图表不显示
**原因**：网络问题或 TradingView 服务异常
**解决**：
- 检查网络连接
- 刷新浏览器/组件
- 更换股票代码

---

## 📚 相关资源

### 官方文档
- [vnpy 官方文档](https://www.vnpy.com/docs)
- [TradingView 文档](https://www.tradingview.com/chart/)
- [Flask 文档](https://flask.palletsprojects.com/)

### 示例代码
- Webhook 服务器：`tradingview_webhook_server.py`
- 整合界面：`tradingview_vnpy_integrated.py`
- vnpy 网关：`vnpy_gateway_eastmoney.py`

---

## 🎓 进阶学习

### 1. 策略开发
- 学习 Pine Script（TradingView 脚本语言）
- 开发自定义技术指标
- 回测交易策略

### 2. 系统优化
- 使用 Redis 缓存数据
- 添加数据库存储交易记录
- 实现分布式部署

### 3. 风险管理
- 实现仓位管理
- 添加资金管理模块
- 开发风险监控系统

---

## ✅ 总结

**TradingView + vnpy 整合方案已完成！**

### 核心优势
- ✅ 专业图表 + 强大交易
- ✅ 警报自动化执行
- ✅ 完整的风控体系
- ✅ 灵活的扩展能力

### 立即开始
1. 运行整合界面：`python tradingview_vnpy_integrated.py`
2. 配置 TradingView Webhook
3. 创建交易策略警报
4. 开始自动化交易！

---

**祝你交易顺利！** 📈💰
