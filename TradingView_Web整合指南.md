# TradingView Web 整合 - 使用指南

## 🎯 架构说明

这是一个以 **TradingView Web 界面为主框架**，整合 **vnpy 完整功能**的专业量化交易平台。

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                   Web 浏览器                              │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │         TradingView 图表 (全屏)                   │  │
│  │                                                  │  │
│  │  - 专业 K 线图                                   │  │
│  │  - 100+ 技术指标                                 │  │
│  │  - 画线工具                                      │  │
│  │  - Pine Script 策略                             │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌────────────────┐                                   │
│  │  vnpy 控制面板  │ (浮动/侧边栏)                     │
│  │                 │                                   │
│  │  - 连接配置      │                                   │
│  │  - 快速下单      │                                   │
│  │  - 账户信息      │                                   │
│  │  - 持仓管理      │                                   │
│  │  - 订单管理      │                                   │
│  └────────────────┘                                   │
└─────────────────────────────────────────────────────────┘
                          ↕
                    HTTP/WebSocket
                          ↕
┌─────────────────────────────────────────────────────────┐
│              Flask Web 服务器                             │
│                                                         │
│  - REST API 接口                                        │
│  - WebSocket 实时通信                                   │
│  - 静态文件服务                                         │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │           vnpy 交易引擎                        │      │
│  │                                               │      │
│  │  - MainEngine                                 │      │
│  │  - EventEngine                                │      │
│  │  - 订单管理                                    │      │
│  │  - 风险控制                                    │      │
│  └──────────────────────────────────────────────┘      │
│                                                         │
│  ┌──────────────────────────────────────────────┐      │
│  │         东财交易网关 (EM)                      │      │
│  │                                               │      │
│  │  - A 股交易接口                               │      │
│  │  - 实时行情                                   │      │
│  │  - 账户查询                                   │      │
│  └──────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────┘
                          ↕
                    HTTP API
                          ↕
┌─────────────────────────────────────────────────────────┐
│              东方财富 交易接口                            │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 启动服务器

```bash
cd /Users/shuai
./start_web_trading.sh
```

或者：

```bash
cd /Users/shuai
source vnpy_env/bin/activate
python tradingview_web_server.py
```

### 2. 访问界面

打开浏览器，访问：**http://localhost:5000**

---

## 💡 使用说明

### 界面布局

```
┌──────────────────────────────────────────────────────────┐
│  TradingView 图表（左侧全屏）     │  vnpy 控制面板（右侧）  │
│                                    │                      │
│  - 专业 K 线图                     │  ┌──────────────────┐ │
│  - 技术指标                        │  │  📡 连接配置     │ │
│  - 绘图工具                        │  │  📈 快速下单     │ │
│  - 警报管理                        │  │  💰 账户信息     │ │
│                                   │  │  📊 持仓信息     │ │
│                                   │  │  📋 订单管理     │ │
│                                   │  │  📝 系统日志     │ │
│                                   │  └──────────────────┘ │
└──────────────────────────────────────────────────────────┘
```

### 功能说明

#### 1. 连接配置
- 填入东财账号信息
- **推荐使用 Cookie**（更稳定）
- 点击"连接网关"

#### 2. 快速下单
- 输入股票代码（如：600000）
- 选择交易所（上交所/深交所/北交所）
- 输入价格和数量
- 点击"买入"或"卖出"

#### 3. 账户信息
- 实时显示账户余额
- 可用资金查询

#### 4. 持仓信息
- 查看当前持仓
- 持仓数量统计

#### 5. 订单管理
- 查看待成交订单
- 订单状态跟踪

#### 6. 系统日志
- 实时显示操作日志
- 成交回报信息
- 系统状态通知

---

## 🔧 API 接口文档

### 基础 URL
```
http://localhost:5000/api
```

### 接口列表

#### 1. 系统状态
```http
GET /api/status
```

**响应**：
```json
{
  "status": "running",
  "vnpy_connected": true,
  "gateway_connected": false
}
```

#### 2. 连接网关
```http
POST /api/connect
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password",
  "cookie": "your_cookie"
}
```

**响应**：
```json
{
  "success": true,
  "message": "连接成功"
}
```

#### 3. 获取账户
```http
GET /api/account
```

**响应**：
```json
{
  "accounts": [
    {
      "accountid": "EM_account",
      "balance": 100000.0,
      "available": 95000.0
    }
  ]
}
```

#### 4. 获取持仓
```http
GET /api/position
```

**响应**：
```json
{
  "positions": [
    {
      "symbol": "600000",
      "volume": 100,
      "available": 100,
      "price": 10.5
    }
  ]
}
```

#### 5. 获取订单
```http
GET /api/orders
```

#### 6. 发送订单
```http
POST /api/order
Content-Type: application/json

{
  "symbol": "600000",
  "exchange": "SSE",
  "direction": "LONG",
  "type": "LIMIT",
  "price": 10.5,
  "volume": 100
}
```

**参数说明**：
- `symbol`: 股票代码
- `exchange`: SSE(上交所)/SZSE(深交所)/BSE(北交所)
- `direction`: LONG(买入)/SHORT(卖出)
- `type`: LIMIT(限价)/MARKET(市价)
- `price`: 价格
- `volume`: 数量（股）

#### 7. 撤销订单
```http
POST /api/cancel
Content-Type: application/json

{
  "orderid": "EM_0001",
  "symbol": "600000",
  "exchange": "SSE"
}
```

#### 8. 订阅行情
```http
POST /api/subscribe
Content-Type: application/json

{
  "symbol": "600000",
  "exchange": "SSE"
}
```

---

## 🔌 WebSocket 事件

### 连接服务器
```javascript
const socket = io('http://localhost:5000');

socket.on('connect', () => {
    console.log('已连接');
});
```

### 实时事件

#### tick - 行情推送
```javascript
socket.on('tick', (data) => {
    console.log('行情:', data);
    // { symbol: '600000', last_price: 10.5, volume: 100 }
});
```

#### trade - 成交推送
```javascript
socket.on('trade', (data) => {
    console.log('成交:', data);
    // { orderid: 'EM.EM_0001', symbol: '600000', price: 10.5, volume: 100 }
});
```

#### order - 订单状态
```javascript
socket.on('order', (data) => {
    console.log('订单:', data);
    // { orderid: 'EM.EM_0001', status: '全成' }
});
```

#### account - 账户更新
```javascript
socket.on('account', (data) => {
    console.log('账户:', data);
    // { accounts: [...] }
});
```

#### position - 持仓更新
```javascript
socket.on('position', (data) => {
    console.log('持仓:', data);
    // { positions: [...] }
});
```

### 刷新数据
```javascript
socket.emit('refresh_data');
```

---

## 📸 界面截图说明

### 主界面
- **左侧 100%**: TradingView 专业图表
- **右侧 350px**: vnpy 控制面板（可滚动）
- **实时更新**: WebSocket 推送数据
- **暗色主题**: 适合长时间交易

### TradingView 功能
- 全部技术指标可用
- 画线工具完整
- Pine Script 策略支持
- 多时间周期切换
- 多图表对比

### vnpy 功能
- 一键下单
- 实时持仓查询
- 订单状态跟踪
- 账户资金监控

---

## 🎮 快捷键

| 按键 | 功能 |
|------|------|
| F5 | 刷新数据 |
| Ctrl+R | 刷新图表 |
| Esc | 关闭面板 |

---

## 📊 高级功能

### 1. TradingView 警报联动

在 TradingView 中创建警报，使用 Webhook 触发 vnpy 交易：

**Webhook URL**:
```
http://localhost:5000/webhook
```

**消息格式**:
```json
{
  "symbol": "600000",
  "action": "buy",
  "price": 10.5,
  "volume": 100
}
```

### 2. 自定义策略

在 TradingView 使用 Pine Script 编写策略，然后通过警报触发 vnpy 执行。

**示例 Pine Script**:
```pinescript
//@version=5
strategy("MA Cross")

ma1 = ta.sma(close, 10)
ma2 = ta.sma(close, 20)

if (crossover(ma1, ma2))
    strategy.entry("Long", strategy.long)

// 触发警报
alert("Buy Signal", alert.freq_once_per_bar_close)
```

### 3. 多屏显示

- **主屏**: TradingView 图表（全屏）
- **副屏**: vnpy 控制面板
- 使用浏览器的"投屏"功能分离显示

---

## 🔐 安全建议

1. **使用 HTTPS**（生产环境）
2. **设置 API 密钥**
3. **限制访问 IP**
4. **定期更换 Cookie**
5. **使用模拟账户测试**

---

## 🐛 故障排查

### 问题 1: 无法连接服务器
**解决**:
- 检查防火墙设置
- 确认端口 5000 未被占用
- 查看服务器日志

### 问题 2: 订单未执行
**解决**:
- 检查网关连接状态
- 确认账户资金充足
- 验证股票代码正确

### 问题 3: 数据不更新
**解决**:
- 刷新浏览器页面
- 检查 WebSocket 连接
- 点击"刷新数据"按钮

---

## 📚 相关文件

| 文件 | 说明 |
|------|------|
| `tradingview_web_server.py` | Web 服务器 |
| `templates/tradingview_integrated.html` | 前端界面 |
| `vnpy_gateway_eastmoney.py` | 东财网关 |
| `start_web_trading.sh` | 启动脚本 |

---

## ✅ 优势对比

### 与之前的桌面版对比

| 特性 | 桌面版 | **Web 版** ✅ |
|------|--------|--------------|
| 界面框架 | PyQt 桌面应用 | **TradingView Web** |
| 图表功能 | vnpy 内置图表 | **TradingView 专业图表** |
| 技术指标 | 有限 | **100+ 指标** |
| 绘图工具 | 基础 | **完整工具集** |
| Pine Script | 不支持 | **✅ 支持** |
| 跨平台 | 需要安装 | **浏览器直接访问** |
| 远程访问 | 需要远程桌面 | **✅ Web 访问** |
| 移动端 | 不支持 | **✅ 支持移动浏览器** |

---

## 🎉 总结

**这是一个真正的 TradingView 主导的量化交易平台！**

- ✅ TradingView 专业图表
- ✅ vnpy 强大交易功能
- ✅ Web 界面，跨平台访问
- ✅ 实时数据推送
- ✅ 完整的 API 接口

**立即开始使用！** 🚀
