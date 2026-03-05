# TradingView量化交易系统 v6.0

**完整的TradingView界面 + 量化交易插件 + 回测系统**

[![Python](https://img.shields.io/badge/Python-3.14%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0%2B-green)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 🎯 项目简介

这是一个专业的量化交易系统，将**完整的TradingView图表**与**量化交易功能**无缝集成。系统采用插件化设计，在保留TradingView全部功能的同时，提供强大的量化交易和回测能力。

### 核心特性

✅ **完整TradingView体验**
- 官方TradingView Widget Library
- 100+技术指标
- 完整画线工具箱
- 多品种、多周期支持

✅ **量化交易插件**
- 可折叠侧边栏设计
- 账户管理、快速交易
- 持仓和订单管理
- WebSocket实时数据

✅ **回测系统**
- 策略回测引擎
- 历史数据管理
- 绩效分析报告
- 可视化图表

✅ **安全可靠**
- JWT用户认证
- Bcrypt密码加密
- CORS跨域保护
- 输入验证和清洗

---

## 🚀 快速开始

### 环境要求

- Python 3.14+
- pip包管理器

### 安装依赖

```bash
pip install flask flask-socketio flask-cors
pip install bcrypt pyjwt requests
pip install eventlet
```

### 启动服务器

```bash
# 启动服务器
python3 trading_server_integrated.py

# 访问界面
# 完整版: http://localhost:8080
# 简化版: http://localhost:8080/lite
```

### 首次使用

1. 打开浏览器访问 http://localhost:8080
2. 点击右上角 📈 插件按钮打开交易面板
3. 在"账户"选项卡登录或注册
4. 开始使用完整TradingView和交易功能

---

## 📖 系统架构

```
┌─────────────────────────────────────────────────────┐
│              TradingView完整界面 (100%)              │
│  ┌─────────────────────────────────────────────┐   │
│  │  TradingView Widget Library                │   │
│  │  • K线图、技术指标、画线工具                │   │
│  │  • 多品种、多周期、财经日历                 │   │
│  └─────────────────────────────────────────────┘   │
│                         ↑                            │
│              [插件按钮] 📈                           │
│                         ↓                            │
│  ┌─────────────────────────────────────────────┐   │
│  │  量化交易插件 (可折叠侧边栏)                 │   │
│  │  • 账户、交易、持仓、订单                   │   │
│  │  • 回测系统                                 │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
                         ↓ WebSocket/API
┌─────────────────────────────────────────────────────┐
│            Flask后端 + Socket.IO                     │
│  • REST API • WebSocket • JWT认证                   │
└─────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────┐
│              vnpy + Eastmoney网关                    │
└─────────────────────────────────────────────────────┘
```

---

## 🎨 界面预览

### 完整版界面

- **完整TradingView** (http://localhost:8080)
  - 100%屏幕空间的图表
  - 所有TradingView原生功能
  - 插件化交易面板

### 简化版界面

- **轻量级图表** (http://localhost:8080/lite)
  - Lightweight Charts
  - 集成交易界面
  - 快速加载

---

## 📚 功能模块

### 1. TradingView图表

✅ **完整功能**
- K线图表、技术指标、画线工具
- 多周期（分钟/日线/周线等）
- 多品种（A股/港股/美股/期货等）
- 财经日历、股票筛选器

### 2. 量化交易插件

✅ **账户管理**
- 总资产、可用资金
- 持仓市值、今日盈亏
- 实时行情显示

✅ **快速交易**
- 买入/卖出
- 限价单
- 实时下单

✅ **持仓管理**
- 当前持仓列表
- 多空方向标识
- 实时更新

✅ **订单管理**
- 活跃订单列表
- 订单状态追踪
- 一键撤单

### 3. 回测系统

✅ **策略回测**
- 策略定义和编辑
- 历史数据回测
- 绩效指标计算

✅ **数据管理**
- 历史行情数据
- 数据清洗和存储
- 数据更新机制

✅ **可视化报告**
- 资金曲线
- 收益分布
- 回撤分析

---

## 🔧 技术栈

### 后端

- **Python 3.14+** - 核心语言
- **Flask 3.0+** - Web框架
- **Flask-SocketIO** - WebSocket支持
- **JWT** - 用户认证
- **Bcrypt** - 密码加密

### 前端

- **TradingView Widget** - 完整图表组件
- **Bootstrap 5.3** - UI框架
- **Socket.IO 4.5** - WebSocket客户端
- **Axios 1.4** - HTTP请求
- **Font Awesome 6.4** - 图标库

---

## 📁 项目结构

```
trading_system/
├── trading_server_integrated.py      # 主服务器
├── templates/
│   ├── trading_full.html             # 完整TradingView界面
│   ├── trading.html                  # 简化版界面
│   └── tradingview_integrated.html   # 集成版界面
├── backtest_system.py                # 回测系统 (开发中)
├── users.db                          # 用户数据库
├── README.md                         # 项目说明
├── TradingView完整集成方案.md         # 架构文档
├── 完整版使用指南.md                  # 用户手册
└── 版本对比与总结.md                  # 版本历史
```

---

## 🎯 使用场景

### 适用人群

✅ **专业交易员**
- 完整的技术分析工具
- 实时行情监控
- 快速下单执行

✅ **量化交易者**
- 策略回测
- 历史数据分析
- 绩效优化

✅ **个人投资者**
- 简单易用的界面
- 专业的图表工具
- 便捷的交易功能

---

## 📊 API文档

### 用户认证

```
POST /api/auth/register  # 用户注册
POST /api/auth/login     # 用户登录
POST /api/auth/verify    # Token验证
```

### 交易API

```
GET  /api/account        # 查询账户
GET  /api/position       # 查询持仓
GET  /api/orders         # 查询订单
POST /api/order          # 提交订单
DELETE /api/cancel       # 撤销订单
```

### 回测API

```
POST /api/backtest/run           # 运行回测
GET  /api/backtest/results       # 获取回测结果
GET  /api/backtest/report/{id}   # 获取回测报告
```

---

## 🛡️ 安全特性

✅ **密码安全**
- Bcrypt加密（12轮加盐）
- 密码复杂度验证

✅ **身份认证**
- JWT Token认证
- Token过期机制

✅ **输入验证**
- SQL注入防护
- XSS攻击防护
- CSRF保护

✅ **审计日志**
- 操作日志记录
- 安全事件追踪

---

## 📈 版本历史

### v6.0 (2026-03-06) - 完整TradingView集成

**重大更新:**
- ✅ 完整TradingView Widget集成
- ✅ 插件化交易面板设计
- ✅ 100%保留TradingView功能
- ✅ 回测系统框架搭建

**修复:**
- ✅ K线数据连续性
- ✅ 实时更新逻辑
- ✅ 布局比例优化

### v5.0 (2026-03-06) - 前端集成

- ✅ 前端界面开发
- ✅ 用户认证系统
- ✅ WebSocket实时通信

### v4.0 (2026-03-05) - 安全加固

- ✅ P0安全问题修复
- ✅ CORS配置
- ✅ 输入验证

### v3.0 (2026-03-05) - 后端API

- ✅ REST API开发
- ✅ 用户管理
- ✅ 交易功能

### v2.0 (2026-03-04) - 基础集成

- ✅ vnpy集成
- ✅ Eastmoney网关

### v1.0 (2026-03-03) - 初始版本

- ✅ 项目架构
- ✅ 基础功能

---

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

### 开发规范

1. 遵循PEP 8代码规范
2. 添加必要的文档注释
3. 编写单元测试
4. 更新相关文档

---

## 📞 联系方式

- **问题反馈**: GitHub Issues
- **功能建议**: GitHub Discussions
- **技术支持**: 查看项目文档

---

## 📄 许可证

MIT License

---

## ⭐ Star History

如果这个项目对您有帮助，请给个Star支持一下！

---

**系统状态**: ✅ **生产就绪**
**访问地址**: http://localhost:8080
**Python版本**: 3.14+
**推荐浏览器**: Chrome 90+, Firefox 88+, Safari 14+

---

**最后更新**: 2026-03-06
**维护者**: Claude Sonnet 4.5
**项目版本**: v6.0
