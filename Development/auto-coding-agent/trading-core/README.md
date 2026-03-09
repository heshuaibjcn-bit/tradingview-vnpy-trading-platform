# StockAutoTrader - Python Trading Core

股票全自动交易软件的核心交易模块（Python）。

## 功能模块

- **automation/** - 同花顺自动化交易模块
- **strategies/** - 策略引擎和预设策略
- **market/** - 行情数据获取和处理
- **websocket/** - WebSocket 服务器（与前端通信）
- **database/** - 数据库操作（Supabase）
- **risk/** - 风险控制系统
- **backtest/** - 回测系统
- **config/** - 配置管理

## 环境配置

1. 复制 `.env.example` 到 `.env`
2. 填写配置信息

```bash
cp .env.example .env
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 依赖说明

- `pyautogui` - GUI 自动化操作
- `opencv-python` - 图像识别（同花顺窗口元素定位）
- `pandas` / `numpy` - 数据处理
- `websockets` - WebSocket 服务器
- `supabase` - 数据库客户端
- `loguru` - 日志系统
