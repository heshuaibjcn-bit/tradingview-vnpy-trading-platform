# vnpy 操作指南

## 🎯 当前状态

vnpy 已启动，图形界面应该已在桌面打开。

---

## 📋 关于"直接操作界面"的说明

### ⚠️ 我的限制
我作为命令行 AI，**无法直接操作图形界面**：
- ❌ 不能点击按钮
- ❌ 不能输入文本
- ❌ 不能拖动窗口
- ❌ 不能查看 GUI 实时状态

### ✅ 我能做什么
- ✅ 通过 **Python 代码** 操作 vnpy API
- ✅ 自动化执行交易操作
- ✅ 查询数据和分析
- ✅ 创建交易策略

---

## 🖥️ 方式一：手动操作图形界面

### 1. 找到 vnpy 窗口
- 检查 Dock 栏的 Python 图标
- 使用 `Cmd + Tab` 切换应用
- 窗口标题应该是 "vnpy 4.0"

### 2. 配置东财账号
```
1. 点击菜单【系统】→【连接】
2. 网关选择：【EM (Eastmoney)】
3. 填写配置：
   - username: 你的东财账号
   - password: 你的密码
   - cookie: 你的 Cookie（推荐）
4. 点击【连接】按钮
```

### 3. 主要功能区域
- **左侧**：交易面板（下单、撤单）
- **中间**：行情显示
- **右侧**：账户信息、持仓
- **底部**：日志输出

---

## 🐍 方式二：通过代码自动操作（推荐）

### 快速演示脚本

我已经创建了自动化脚本：`/Users/shuai/vnpy_auto_demo.py`

#### 运行演示：
```bash
cd /Users/shuai
source vnpy_env/bin/activate
python vnpy_auto_demo.py
```

#### 完整自动化脚本：`vnpy_auto_操作.py`

```bash
python vnpy_auto_操作.py
```

### 代码操作示例

#### 1. 连接东财网关
```python
from vnpy.trader.engine import MainEngine
from vnpy_gateway_eastmoney import EastmoneyGateway

# 创建引擎
main_engine = MainEngine()
main_engine.add_gateway(EastmoneyGateway)

# 配置并连接
setting = {
    "username": "your_username",
    "password": "your_password",
    "cookie": "your_cookie"
}

main_engine.connect(setting, "EM")
```

#### 2. 订阅行情
```python
from vnpy.trader.object import SubscribeRequest
from vnpy.trader.constant import Exchange

req = SubscribeRequest(
    symbol="600000",      # 浦发银行
    exchange=Exchange.SSE # 上交所
)

main_engine.subscribe(req, "EM")
```

#### 3. 下单
```python
from vnpy.trader.object import OrderRequest
from vnpy.trader.constant import Direction, OrderType

order_req = OrderRequest(
    symbol="600000",
    exchange=Exchange.SSE,
    direction=Direction.LONG,  # 买入
    type=OrderType.LIMIT,      # 限价单
    volume=100,                # 100股
    price=10.50                # 价格
)

vt_orderid = main_engine.send_order(order_req, "EM")
print(f"订单已发送: {vt_orderid}")
```

#### 4. 撤单
```python
from vnpy.trader.object import CancelRequest

cancel_req = CancelRequest(
    orderid="EM_0001",   # 订单ID
    symbol="600000",
    exchange=Exchange.SSE
)

main_engine.cancel_order(cancel_req, "EM")
```

#### 5. 查询账户
```python
main_engine.query_account("EM")

# 获取账户数据
accounts = main_engine.get_all_accounts()
for account in accounts:
    print(f"账户: {account.accountid}")
    print(f"余额: {account.balance}")
    print(f"可用: {account.available}")
```

#### 6. 查询持仓
```python
main_engine.query_position("EM")

# 获取持仓数据
positions = main_engine.get_all_positions()
for position in positions:
    print(f"股票: {position.symbol}")
    print(f"持仓: {position.volume}")
    print(f"可用: {position.available}")
```

#### 7. 查询订单
```python
# 所有订单
orders = main_engine.get_all_orders()
for order in orders:
    print(f"订单ID: {order.vt_orderid}")
    print(f"股票: {order.symbol}")
    print(f"状态: {order.status.value}")
```

---

## 📊 方式三：实时数据监控

### 创建监控脚本

创建文件 `/Users/shuai/monitor.py`：

```python
#!/usr/bin/env python3
import time
from vnpy.trader.engine import MainEngine
from vnpy_gateway_eastmoney import EastmoneyGateway

# 创建引擎
main_engine = MainEngine()
main_engine.add_gateway(EastmoneyGateway)

# 连接
setting = {
    "username": "your_username",
    "cookie": "your_cookie"
}
main_engine.connect(setting, "EM")

# 监控循环
while True:
    # 查询账户
    main_engine.query_account("EM")
    accounts = main_engine.get_all_accounts()

    # 查询持仓
    main_engine.query_position("EM")
    positions = main_engine.get_all_positions()

    # 显示信息
    print("\n=== 账户状态 ===")
    for acc in accounts:
        print(f"余额: ¥{acc.balance:.2f}")

    print("\n=== 持仓情况 ===")
    for pos in positions:
        print(f"{pos.symbol}: {pos.volume}股")

    time.sleep(5)  # 每5秒刷新
```

运行监控：
```bash
python monitor.py
```

---

## 🤖 自动化交易策略示例

### 简单均线策略

```python
from vnpy.trader.engine import MainEngine
from vnpy_gateway_eastmoney import EastmoneyGateway
from vnpy.trader.object import OrderRequest
from vnpy.trader.constant import Exchange, Direction, OrderType

# 初始化
main_engine = MainEngine()
main_engine.add_gateway(EastmoneyGateway)

# 配置
setting = {"cookie": "your_cookie"}
main_engine.connect(setting, "EM")

# 策略参数
symbol = "600000"
exchange = Exchange.SSE
buy_threshold = 10.0
sell_threshold = 11.0

# 获取当前价格
tick = main_engine.get_tick(f"{symbol}.{exchange.value}")

if tick:
    current_price = tick.last_price

    # 买入条件
    if current_price < buy_threshold:
        order = OrderRequest(
            symbol=symbol,
            exchange=exchange,
            direction=Direction.LONG,
            type=OrderType.LIMIT,
            volume=100,
            price=current_price
        )
        main_engine.send_order(order, "EM")
        print(f"买入信号: {current_price}")

    # 卖出条件
    elif current_price > sell_threshold:
        # 查询持仓
        positions = main_engine.get_all_positions()

        for pos in positions:
            if pos.symbol == symbol and pos.available > 0:
                order = OrderRequest(
                    symbol=symbol,
                    exchange=exchange,
                    direction=Direction.SHORT,
                    type=OrderType.LIMIT,
                    volume=pos.available,
                    price=current_price
                )
                main_engine.send_order(order, "EM")
                print(f"卖出信号: {current_price}")
```

---

## 🔧 获取 Cookie 的方法

### 步骤：
1. 浏览器打开 https://eastmoney.com
2. 登录账号
3. 按 `F12` 打开开发者工具
4. 切换到 `Network` 标签
5. 刷新页面
6. 点击任意请求
7. 查看 `Request Headers`
8. 复制 `Cookie` 的值

### Cookie 格式：
```
qtpi=abc123; emshistory=xxx; sessionid=yyy; ...
```

---

## 📝 总结

### 推荐操作方式：
1. **开发阶段**：使用 Python 代码自动化
2. **日常使用**：GUI 界面手动操作
3. **策略运行**：代码自动化 + 后台监控

### 文件位置：
- GUI 启动脚本：`~/start_vnpy.py`
- 自动化演示：`~/vnpy_auto_demo.py`
- 完整自动化：`~/vnpy_auto_操作.py`
- 使用文档：`~/vnpy_使用说明.md`

---

**需要我帮你编写特定的自动化脚本吗？** 🤖
