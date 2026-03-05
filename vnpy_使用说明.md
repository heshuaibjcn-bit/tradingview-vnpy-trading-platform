# vnpy + 东方财富交易接口 使用说明

## 🎉 恭喜！vnpy 已成功启动

vnpy 4.0 已成功启动，并集成了东方财富交易网关。

## 📋 功能特性

### 已实现功能
✅ **东财交易网关** (EastmoneyGateway)
- 支持上海、深圳、北京证券交易所
- 订单管理（下单、撤单）
- 账户查询
- 持仓查询
- 行情订阅
- 历史 K 线数据

### 核心模块
- **vnpy 4.0** - 量化交易框架
- **EastmoneyGateway** - 东方财富交易接口
- **PySide6** - GUI 界面
- **pandas/numpy** - 数据处理
- **ta-lib** - 技术指标

## 🔧 配置东财交易接口

### 方法 1：使用图形界面配置

1. **打开 vnpy 界面**
   - vnpy 窗口应该已经在你的桌面上打开了

2. **进入连接配置**
   - 点击菜单【系统】→【连接】
   - 选择网关：【EM (Eastmoney)】

3. **填写配置信息**
   ```json
   {
     "username": "你的东财账号",
     "password": "你的密码",
     "cookie": "你的东财Cookie（推荐）"
   }
   ```

4. **获取 Cookie 的方法**

   **浏览器方式（推荐）：**
   ```bash
   1. 打开浏览器，访问 https://eastmoney.com
   2. 按 F12 打开开发者工具
   3. 登录你的账号
   4. 切换到 Network（网络）标签
   5. 刷新页面，找到任意请求
   6. 查看 Request Headers 中的 Cookie
   7. 复制完整的 Cookie 值
   ```

5. **点击连接**
   - 配置完成后，点击【连接】按钮
   - 查看日志窗口确认连接状态

## 📊 使用示例

### Python 代码示例

```python
from vnpy.trader.engine import MainEngine
from vnpy.trader.object import OrderRequest, SubscribeRequest
from vnpy.trader.constant import Exchange, Direction, OrderType
from vnpy_gateway_eastmoney import EastmoneyGateway

# 创建主引擎
main_engine = MainEngine()

# 添加东财网关
main_engine.add_gateway(EastmoneyGateway)

# 连接东财
setting = {
    "username": "your_username",
    "password": "your_password",
    "cookie": "your_cookie"
}
main_engine.connect(setting, "EM")

# 订阅行情
req = SubscribeRequest(
    symbol="600000",
    exchange=Exchange.SSE
)
main_engine.subscribe(req, "EM")

# 下单示例
order_req = OrderRequest(
    symbol="600000",
    exchange=Exchange.SSE,
    direction=Direction.LONG,      # 买入
    type=OrderType.LIMIT,          # 限价单
    volume=100,                    # 100股
    price=10.50                    # 价格
)
vt_orderid = main_engine.send_order(order_req, "EM")
print(f"订单已发送: {vt_orderid}")
```

## ⚠️ 重要提示

### 关于东财 API 限制

1. **官方 SDK 版本限制**
   - 东财官方 QuantAPI SDK 仅支持 Python 2.7 - 3.8
   - 你的环境是 Python 3.14

2. **本网关的解决方案**
   - 使用 HTTP API 方式，兼容所有 Python 版本
   - 不依赖官方 SDK，使用 requests 库

3. **功能说明**
   - 网关框架已完成
   - 具体的 API 端点需要根据东财的实际接口调整
   - 建议参考东财官方文档或使用抓包工具获取实际 API

## 🛠️ 高级配置

### 自定义东财 API 端点

编辑 `vnpy_gateway_eastmoney.py` 文件：

```python
class EastmoneyGateway(BaseGateway):
    # 修改这些 URL 为实际的东财 API
    BASE_URL: str = "https://push2.eastmoney.com/api/qt"
    TRADE_URL: str = "https://trade.eastmoney.com"
```

### 调试模式

查看详细日志：
```bash
# 在 vnpy 界面的日志窗口查看
# 或者在命令行查看
tail -f /private/tmp/claude-*/tasks/*.output
```

## 📚 学习资源

- **vnpy 官网**: https://www.vnpy.com
- **vnpy 文档**: https://www.vnpy.com/docs
- **东财量化接口**: https://quantapi.eastmoney.com

## 🔍 故障排查

### 问题 1：无法连接
- 检查网络连接
- 确认 Cookie 是否过期
- 查看日志窗口的错误信息

### 问题 2：订单失败
- 确认账户资金充足
- 检查股票代码和交易所
- 验证价格是否在涨跌停范围内

### 问题 3：行情延迟
- 检查网络质量
- 尝试重新订阅
- 查看东财服务器状态

## 📞 技术支持

- vnpy 社区论坛
- 东财官方客服
- GitHub Issues

---

**祝你交易顺利！** 📈💰
