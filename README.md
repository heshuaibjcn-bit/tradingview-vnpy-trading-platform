# TradingView + vnpy 专业量化交易平台

基于 Web 的专业量化交易平台，以 TradingView 图表为主框架，完整整合 vnpy 底层交易功能。

## ✨ 特性

- 🎯 **TradingView 主框架** - 占据界面 70%，提供专业图表和技术分析
- 🚀 **vnpy 底层功能** - 完整的量化交易引擎和订单管理系统
- 💹 **Eastmoney 接口** - 支持国内 A 股交易（上交所/深交所/北交所）
- 🌐 **Web 界面** - 基于 Flask + Socket.IO 的现代 Web 架构
- 📊 **实时数据** - WebSocket 支持实时行情和交易推送
- 🎨 **暗色主题** - 专业交易风格，适合长时间使用
- ✅ **完整测试** - 100% 自动化测试通过率

## 📋 系统要求

- Python 3.8+
- vnpy 4.0+
- Flask 2.0+
- Chrome/Edge/Firefox 浏览器

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install vnpy flask flask-socketio requests
```

### 2. 启动服务器

```bash
python tradingview_web_server_v2.py
```

### 3. 访问界面

打开浏览器访问: http://localhost:8080

## 📁 项目结构

```
tradingview-vnpy-trading-platform/
├── vnpy_gateway_eastmoney.py       # Eastmoney 交易网关
├── tradingview_web_server_v2.py    # Flask Web 服务器
├── templates/
│   └── tradingview_integrated.html # Web 前端界面
├── start_vnpy.py                   # vnpy 启动脚本
├── vnpy_eastmoney_config.json      # Eastmoney 配置文件
├── test_*.py                       # 自动化测试套件
└── docs/                           # 项目文档
```

## 🔧 配置

编辑 `vnpy_eastmoney_config.json` 配置 Eastmoney 账号：

```json
{
  "username": "your_username",
  "password": "your_password",
  "app_id": "your_app_id"
}
```

## 🧪 测试

运行自动化测试：

```bash
# Selenium 自动化测试
python test_web_automation_selenium.py

# 视觉测试
python test_visual_inspector.py

# API 测试
python test_eastmoney_api.py
```

## 📊 功能模块

### TradingView 图表
- K 线图显示
- 技术指标分析
- 多时间周期
- 绘图工具

### vnpy 控制面板
- 连接配置
- 快速下单
- 账户信息
- 持仓管理
- 订单管理
- 系统日志

### 交易功能
- 限价单/市价单
- 条件单
- 止盈止损
- 持仓查询
- 成交记录

## 🔌 API 接口

### REST API

- `GET /api/status` - 系统状态
- `POST /api/connect` - 连接网关
- `GET /api/account` - 账户信息
- `GET /api/position` - 持仓信息
- `GET /api/orders` - 订单列表
- `POST /api/order` - 下单
- `DELETE /api/cancel` - 撤单

### WebSocket 事件

- `tick` - 实时行情
- `trade` - 成交推送
- `order` - 订单状态
- `account` - 账户变动
- `position` - 持仓变动

## 📈 测试结果

- ✅ Selenium 自动化: 7/7 通过 (100%)
- ✅ API 端点: 4/4 通过 (100%)
- ✅ 视觉测试: 通过
- ✅ 响应式设计: 通过

## 📄 文档

- [项目完成总结](项目完成总结.md)
- [Web 整合指南](TradingView_Web整合指南.md)
- [vnpy 操作指南](vnpy操作指南.md)
- [自主调试报告](autonomous_debugging_report.md)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📜 许可

MIT License

## 📞 联系

如有问题，请提交 Issue。

---

**⚠️ 免责声明**: 本项目仅供学习研究使用，不构成投资建议。使用本软件进行实盘交易的风险由使用者自行承担。
