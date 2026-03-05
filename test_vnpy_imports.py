#!/usr/bin/env python3
"""
vnpy 核心模块导入测试
验证所有关键模块能否正确导入
"""
import sys

print("=" * 60)
print("vnpy 核心模块导入测试")
print("=" * 60)

# 测试结果
results = {}

def test_import(module_name, description):
    """测试模块导入"""
    try:
        exec(f"import {module_name}")
        results[module_name] = True
        print(f"✅ {description}: {module_name}")
        return True
    except Exception as e:
        results[module_name] = False
        print(f"❌ {description}: {module_name}")
        print(f"   错误: {str(e)}")
        return False

# 核心模块测试
print("\n1. 核心模块测试")
print("-" * 60)
test_import("vnpy", "vnpy 主包")
test_import("vnpy.trader", "trader 交易模块")
test_import("vnpy.event", "event 事件模块")
test_import("vnpy.chart", "chart 图表模块")
test_import("vnpy.alpha", "alpha 量化模块")

# trader 子模块测试
print("\n2. Trader 子模块测试")
print("-" * 60)
test_import("vnpy.trader.engine", "MainEngine 主引擎")
test_import("vnpy.trader.gateway", "BaseGateway 网关基类")
test_import("vnpy.trader.object", "数据对象")
test_import("vnpy.trader.constant", "常量定义")
test_import("vnpy.trader.ui", "UI 界面")
test_import("vnpy.trader.app", "应用基类")

# 数据对象测试
print("\n3. 数据对象测试")
print("-" * 60)
test_import("vnpy.trader.object.TickData", "TickData")
test_import("vnpy.trader.object.BarData", "BarData")
test_import("vnpy.trader.object.OrderData", "OrderData")
test_import("vnpy.trader.object.TradeData", "TradeData")
test_import("vnpy.trader.object.PositionData", "PositionData")
test_import("vnpy.trader.object.AccountData", "AccountData")
test_import("vnpy.trader.object.ContractData", "ContractData")

# 依赖库测试
print("\n4. 依赖库测试")
print("-" * 60)
test_import("pandas", "pandas 数据处理")
test_import("numpy", "numpy 数值计算")
test_import("requests", "requests HTTP 库")
test_import("PySide6", "PySide6 GUI 框架")
test_import("pyqtgraph", "pyqtgraph 图形库")
test_import("plotly", "plotly 交互图表")
test_import("talib", "talib 技术分析")

# 统计结果
print("\n" + "=" * 60)
print("测试结果统计")
print("=" * 60)
total = len(results)
passed = sum(results.values())
failed = total - passed

print(f"总计: {total} 个模块")
print(f"通过: {passed} 个 ✅")
print(f"失败: {failed} 个 ❌")
print(f"成功率: {passed/total*100:.1f}%")

# 详细错误信息
if failed > 0:
    print("\n失败的模块:")
    for module, success in results.items():
        if not success:
            print(f"  - {module}")

# 返回值
sys.exit(0 if failed == 0 else 1)
