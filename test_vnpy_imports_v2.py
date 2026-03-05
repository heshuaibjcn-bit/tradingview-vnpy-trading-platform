#!/usr/bin/env python3
"""
vnpy 核心模块导入测试 v2
修正导入方式
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
        print(f"✅ {description}")
        return True
    except Exception as e:
        results[module_name] = False
        print(f"❌ {description}")
        print(f"   错误: {str(e)}")
        return False

def test_from_import(module_path, class_name, description):
    """测试从模块导入类"""
    try:
        exec(f"from {module_path} import {class_name}")
        results[f"{module_path}.{class_name}"] = True
        print(f"✅ {description}")
        return True
    except Exception as e:
        results[f"{module_path}.{class_name}"] = False
        print(f"❌ {description}")
        print(f"   错误: {str(e)}")
        return False

# 核心模块测试
print("\n1. 核心模块测试")
print("-" * 60)
test_import("vnpy", "vnpy 主包")
test_import("vnpy.trader", "trader 交易模块")
test_import("vnpy.event", "event 事件模块")
test_import("vnpy.chart", "chart 图表模块")

# trader 子模块测试
print("\n2. Trader 子模块测试")
print("-" * 60)
test_import("vnpy.trader.engine", "MainEngine 主引擎")
test_import("vnpy.trader.gateway", "BaseGateway 网关基类")
test_import("vnpy.trader.object", "数据对象模块")
test_import("vnpy.trader.constant", "常量定义")
test_import("vnpy.trader.ui", "UI 界面")
test_import("vnpy.trader.app", "应用基类")

# 数据对象测试（修正导入方式）
print("\n3. 数据对象测试")
print("-" * 60)
test_from_import("vnpy.trader.object", "TickData", "TickData")
test_from_import("vnpy.trader.object", "BarData", "BarData")
test_from_import("vnpy.trader.object", "OrderData", "OrderData")
test_from_import("vnpy.trader.object", "TradeData", "TradeData")
test_from_import("vnpy.trader.object", "PositionData", "PositionData")
test_from_import("vnpy.trader.object", "AccountData", "AccountData")
test_from_import("vnpy.trader.object", "ContractData", "ContractData")
test_from_import("vnpy.trader.object", "OrderRequest", "OrderRequest")
test_from_import("vnpy.trader.object", "CancelRequest", "CancelRequest")
test_from_import("vnpy.trader.object", "SubscribeRequest", "SubscribeRequest")

# 常量测试
print("\n4. 常量测试")
print("-" * 60)
test_from_import("vnpy.trader.constant", "Exchange", "Exchange 交易所")
test_from_import("vnpy.trader.constant", "Direction", "Direction 方向")
test_from_import("vnpy.trader.constant", "OrderType", "OrderType 订单类型")
test_from_import("vnpy.trader.constant", "Status", "Status 状态")
test_from_import("vnpy.trader.constant", "Product", "Product 产品类型")

# 依赖库测试
print("\n5. 依赖库测试")
print("-" * 60)
test_import("pandas", "pandas 数据处理")
test_import("numpy", "numpy 数值计算")
test_import("requests", "requests HTTP 库")
test_import("PySide6", "PySide6 GUI 框架")
test_import("pyqtgraph", "pyqtgraph 图形库")
test_import("plotly", "plotly 交互图表")
test_import("talib", "talib 技术分析")

# 东财网关测试
print("\n6. 东财网关测试")
print("-" * 60)
test_from_import("vnpy_gateway_eastmoney", "EastmoneyGateway", "EastmoneyGateway 东财网关")

# 统计结果
print("\n" + "=" * 60)
print("测试结果统计")
print("=" * 60)
total = len(results)
passed = sum(results.values())
failed = total - passed

print(f"总计: {total} 个测试")
print(f"通过: {passed} 个 ✅")
print(f"失败: {failed} 个 ❌")
print(f"成功率: {passed/total*100:.1f}%")

# 返回值
sys.exit(0 if failed == 0 else 1)
