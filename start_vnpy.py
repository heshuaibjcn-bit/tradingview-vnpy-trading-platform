#!/usr/bin/env python3
"""
vnpy 启动脚本 - 集成东方财富交易接口
"""
import sys
from pathlib import Path

# 添加当前目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

from vnpy.trader.app import BaseApp
from vnpy.trader.ui import QtCore, QtGui, QtWidgets
from vnpy.trader.engine import MainEngine
from vnpy.trader.ui import MainWindow, create_qapp
from vnpy.trader.object import TickData, BarData, OrderData, TradeData

# 导入东财网关
from vnpy_gateway_eastmoney import EastmoneyGateway


def main():
    """主函数"""
    qapp = create_qapp()

    # 创建主引擎
    main_engine = MainEngine()

    # 添加东财网关
    main_engine.add_gateway(EastmoneyGateway)

    # 创建主窗口
    main_window = MainWindow(main_engine, main_engine.event_engine)
    main_window.showMaximized()

    print("=" * 60)
    print("vnpy 4.0 已启动 - 集成东方财富交易接口")
    print("=" * 60)
    print("支持功能：")
    print("  1. 连接东财交易接口（需要配置账号和 Cookie）")
    print("  2. 查询行情、账户、持仓")
    print("  3. 发送订单、撤单")
    print("  4. 查询历史K线数据")
    print("=" * 60)

    # 运行应用
    qapp.exec()


if __name__ == "__main__":
    main()
