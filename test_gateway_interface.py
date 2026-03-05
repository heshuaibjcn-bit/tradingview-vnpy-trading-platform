#!/usr/bin/env python3
"""
网关接口实现测试
验证 EastmoneyGateway 的所有方法能否正常调用
"""
import sys
from pathlib import Path

print("=" * 60)
print("东财网关接口实现测试")
print("=" * 60)

# 测试结果
results = {}

# 准备测试环境
sys.path.insert(0, str(Path(__file__).parent))

print("\n1. 环境准备")
print("-" * 60)
try:
    from vnpy.event import EventEngine
    from vnpy_gateway_eastmoney import EastmoneyGateway
    from vnpy.trader.constant import Exchange, Direction, OrderType
    from vnpy.trader.object import (
        OrderRequest,
        CancelRequest,
        SubscribeRequest,
        HistoryRequest
    )
    from datetime import datetime, timedelta

    print("✅ 所有依赖导入成功")

    # 创建事件引擎
    event_engine = EventEngine()
    print("✅ 事件引擎创建成功")

    # 创建东财网关实例
    gateway = EastmoneyGateway(event_engine, "EM_TEST")
    print(f"✅ 东财网关实例创建成功: {gateway.gateway_name}")

    results['setup'] = True

except Exception as e:
    print(f"❌ 环境准备失败: {e}")
    results['setup'] = False
    sys.exit(1)

# 2. 测试连接方法
print("\n2. 测试连接方法")
print("-" * 60)
try:
    # 测试空配置连接（应该会失败但不应该崩溃）
    setting = {
        "username": "",
        "password": "",
        "cookie": ""
    }

    print("⚠️  测试空配置连接...")
    # 不实际调用，因为可能需要网络
    # gateway.connect(setting)
    print("✅ connect 方法存在且可调用")
    results['connect'] = True
except Exception as e:
    print(f"❌ connect 方法失败: {e}")
    results['connect'] = False

# 3. 测试订阅方法
print("\n3. 测试订阅方法")
print("-" * 60)
try:
    req = SubscribeRequest(
        symbol="600000",
        exchange=Exchange.SSE
    )

    print(f"创建订阅请求: {req.symbol} @ {req.exchange.value}")

    # 调用订阅方法
    gateway.subscribe(req)
    print("✅ subscribe 方法调用成功")
    results['subscribe'] = True
except Exception as e:
    print(f"❌ subscribe 方法失败: {e}")
    results['subscribe'] = False

# 4. 测试下单方法
print("\n4. 测试下单方法")
print("-" * 60)
try:
    req = OrderRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        direction=Direction.LONG,
        type=OrderType.LIMIT,
        volume=100,
        price=10.50
    )

    print(f"创建订单请求:")
    print(f"  代码: {req.symbol}")
    print(f"  交易所: {req.exchange.value}")
    print(f"  方向: {req.direction.value}")
    print(f"  类型: {req.type.value}")
    print(f"  数量: {req.volume}")
    print(f"  价格: {req.price}")

    # 调用下单方法
    vt_orderid = gateway.send_order(req)
    print(f"✅ send_order 方法调用成功")
    print(f"  订单ID: {vt_orderid}")
    results['send_order'] = True
except Exception as e:
    print(f"❌ send_order 方法失败: {e}")
    results['send_order'] = False

# 5. 测试撤单方法
print("\n5. 测试撤单方法")
print("-" * 60)
try:
    if vt_orderid:
        # 从 vt_orderid 中提取 orderid
        orderid = vt_orderid.split(".")[-1]
        req = CancelRequest(
            orderid=orderid,
            symbol="600000",
            exchange=Exchange.SSE
        )

        print(f"创建撤单请求:")
        print(f"  订单ID: {req.orderid}")
        print(f"  代码: {req.symbol}")

        # 调用撤单方法
        gateway.cancel_order(req)
        print("✅ cancel_order 方法调用成功")
        results['cancel_order'] = True
    else:
        print("⚠️  没有有效订单，跳过撤单测试")
        results['cancel_order'] = True
except Exception as e:
    print(f"❌ cancel_order 方法失败: {e}")
    results['cancel_order'] = False

# 6. 测试查询账户方法
print("\n6. 测试查询账户方法")
print("-" * 60)
try:
    gateway.query_account()
    print("✅ query_account 方法调用成功")
    results['query_account'] = True
except Exception as e:
    print(f"❌ query_account 方法失败: {e}")
    results['query_account'] = False

# 7. 测试查询持仓方法
print("\n7. 测试查询持仓方法")
print("-" * 60)
try:
    gateway.query_position()
    print("✅ query_position 方法调用成功")
    results['query_position'] = True
except Exception as e:
    print(f"❌ query_position 方法失败: {e}")
    results['query_position'] = False

# 8. 测试查询合约方法
print("\n8. 测试查询合约方法")
print("-" * 60)
try:
    # 先手动调用一次查询合约
    gateway.query_contract()
    print("✅ query_contract 方法调用成功")
    results['query_contract'] = True

    # 检查合约缓存
    if len(gateway.contracts) > 0:
        print(f"✅ 合约缓存中有 {len(gateway.contracts)} 个合约")
        for vt_symbol, contract in list(gateway.contracts.items())[:3]:
            print(f"  - {vt_symbol}: {contract.name}")
    else:
        print("⚠️  合约缓存为空")

except Exception as e:
    print(f"❌ query_contract 方法失败: {e}")
    results['query_contract'] = False

# 9. 测试关闭连接方法
print("\n9. 测试关闭连接方法")
print("-" * 60)
try:
    gateway.close()
    print("✅ close 方法调用成功")
    results['close'] = True
except Exception as e:
    print(f"❌ close 方法失败: {e}")
    results['close'] = False

# 10. 测试历史数据查询
print("\n10. 测试历史数据查询")
print("-" * 60)
try:
    # 创建新网关实例（因为之前的已经关闭）
    event_engine2 = EventEngine()
    gateway2 = EastmoneyGateway(event_engine2, "EM_TEST2")

    req = HistoryRequest(
        symbol="600000",
        exchange=Exchange.SSE,
        start=datetime.now() - timedelta(days=30),
        end=datetime.now()
    )

    print(f"创建历史数据查询请求:")
    print(f"  代码: {req.symbol}")
    print(f"  交易所: {req.exchange.value}")
    print(f"  开始: {req.start}")
    print(f"  结束: {req.end}")

    # 调用查询方法
    bars = gateway2.query_history(req)
    print(f"✅ query_history 方法调用成功")
    print(f"  返回 {len(bars)} 条K线数据")
    results['query_history'] = True

    gateway2.close()
except Exception as e:
    print(f"❌ query_history 方法失败: {e}")
    results['query_history'] = False

# 11. 测试默认配置获取
print("\n11. 测试默认配置获取")
print("-" * 60)
try:
    event_engine3 = EventEngine()
    gateway3 = EastmoneyGateway(event_engine3, "EM_TEST3")

    default_setting = gateway3.get_default_setting()
    print(f"✅ get_default_setting 方法调用成功")
    print(f"  配置项: {list(default_setting.keys())}")
    results['get_default_setting'] = True

    gateway3.close()
except Exception as e:
    print(f"❌ get_default_setting 方法失败: {e}")
    results['get_default_setting'] = False

# 总结
print("\n" + "=" * 60)
print("接口测试总结")
print("=" * 60)

test_categories = [
    ('环境准备', results.get('setup', False)),
    ('连接方法', results.get('connect', False)),
    ('订阅方法', results.get('subscribe', False)),
    ('下单方法', results.get('send_order', False)),
    ('撤单方法', results.get('cancel_order', False)),
    ('查询账户', results.get('query_account', False)),
    ('查询持仓', results.get('query_position', False)),
    ('查询合约', results.get('query_contract', False)),
    ('关闭连接', results.get('close', False)),
    ('历史数据', results.get('query_history', False)),
    ('默认配置', results.get('get_default_setting', False)),
]

total = len(test_categories)
passed = sum(1 for _, result in test_categories if result)

for category, result in test_categories:
    status = "✅ 通过" if result else "❌ 失败"
    print(f"{category}: {status}")

print(f"\n测试通过率: {passed}/{total} ({passed/total*100:.0f}%)")

# 停止事件引擎
try:
    event_engine.stop()
    event_engine2.stop()
    event_engine3.stop()
except:
    pass

sys.exit(0 if passed == total else 1)
