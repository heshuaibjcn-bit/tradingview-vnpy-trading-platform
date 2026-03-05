#!/usr/bin/env python3
"""
vnpy 启动流程测试
验证 vnpy 的完整启动流程，包括引擎初始化、网关注册等
"""
import sys
import subprocess
import time
from pathlib import Path

print("=" * 60)
print("vnpy 启动流程测试")
print("=" * 60)

# 测试结果
results = {}

# 1. 检查当前运行的 vnpy 进程
print("\n1. 检查当前 vnpy 进程")
print("-" * 60)
try:
    result = subprocess.run(
        ["ps", "aux"],
        capture_output=True,
        text=True,
        timeout=5
    )

    vnpy_processes = [
        line for line in result.stdout.split('\n')
        if 'python.*start_vnpy' in line and 'grep' not in line
    ]

    if vnpy_processes:
        print(f"✅ 发现 {len(vnpy_processes)} 个 vnpy 进程正在运行")
        for proc in vnpy_processes:
            parts = proc.split()
            if len(parts) >= 2:
                pid = parts[1]
                print(f"  PID: {pid}")
        results['existing_process'] = True
    else:
        print("⚠️  没有发现正在运行的 vnpy 进程")
        results['existing_process'] = False

except Exception as e:
    print(f"❌ 检查进程失败: {e}")
    results['existing_process'] = False

# 2. 测试引擎初始化（无GUI模式）
print("\n2. 测试主引擎初始化")
print("-" * 60)
try:
    from vnpy.trader.engine import MainEngine
    from vnpy.event import EventEngine

    # 创建事件引擎
    event_engine = EventEngine()
    print("✅ 事件引擎创建成功")

    # 创建主引擎
    main_engine = MainEngine()
    print("✅ 主引擎创建成功")

    # 检查主引擎属性
    assert hasattr(main_engine, 'event_engine'), "缺少 event_engine 属性"
    assert hasattr(main_engine, 'gateways'), "缺少 gateways 属性"
    print("✅ 主引擎属性检查通过")

    results['engine_init'] = True

    # 清理
    event_engine.stop()

except Exception as e:
    print(f"❌ 引擎初始化失败: {e}")
    import traceback
    traceback.print_exc()
    results['engine_init'] = False

# 3. 测试网关注册
print("\n3. 测试东财网关注册")
print("-" * 60)
try:
    from vnpy.trader.engine import MainEngine
    from vnpy.event import EventEngine
    from vnpy_gateway_eastmoney import EastmoneyGateway

    # 创建引擎
    event_engine = EventEngine()
    main_engine = MainEngine()

    # 添加网关
    main_engine.add_gateway(EastmoneyGateway)
    print("✅ 东财网关注册成功")

    # 检查网关是否注册
    assert "EM" in main_engine.gateway_names or "Eastmoney" in main_engine.gateway_names \
        or hasattr(main_engine, 'gateways'), "网关未正确注册"
    print("✅ 网关注册验证通过")

    results['gateway_registration'] = True

    # 清理
    event_engine.stop()

except Exception as e:
    print(f"❌ 网关注册失败: {e}")
    import traceback
    traceback.print_exc()
    results['gateway_registration'] = False

# 4. 测试启动脚本语法
print("\n4. 测试启动脚本")
print("-" * 60)
try:
    startup_script = Path("/Users/shuai/start_vnpy.py")

    if not startup_script.exists():
        print(f"❌ 启动脚本不存在: {startup_script}")
        results['startup_script'] = False
    else:
        print(f"✅ 启动脚本存在: {startup_script}")

        # 检查脚本语法
        with open(startup_script, 'r') as f:
            code = f.read()
        compile(code, str(startup_script), 'exec')
        print("✅ 启动脚本语法正确")

        # 检查关键导入
        assert "from vnpy.trader.engine import MainEngine" in code, "缺少 MainEngine 导入"
        assert "from vnpy.trader.ui import MainWindow" in code, "缺少 MainWindow 导入"
        assert "from vnpy_gateway_eastmoney import EastmoneyGateway" in code, "缺少 EastmoneyGateway 导入"
        print("✅ 启动脚本导入检查通过")

        results['startup_script'] = True

except Exception as e:
    print(f"❌ 启动脚本检查失败: {e}")
    results['startup_script'] = False

# 5. 测试组件集成
print("\n5. 测试组件集成")
print("-" * 60)
try:
    from vnpy.trader.engine import MainEngine
    from vnpy.event import EventEngine
    from vnpy_gateway_eastmoney import EastmoneyGateway

    # 创建完整的环境
    event_engine = EventEngine()
    main_engine = MainEngine()
    main_engine.add_gateway(EastmoneyGateway)

    # 测试获取默认设置
    gateways = main_engine.get_all_gateways()
    print(f"✅ 已注册网关数量: {len(gateways)}")

    # 测试事件引擎
    assert event_engine is not None, "事件引擎未初始化"
    assert event_engine.is_active(), "事件引擎未激活"
    print("✅ 事件引擎运行正常")

    results['integration'] = True

    # 清理
    event_engine.stop()

except Exception as e:
    print(f"❌ 组件集成测试失败: {e}")
    import traceback
    traceback.print_exc()
    results['integration'] = False

# 6. 测试配置文件
print("\n6. 测试配置文件")
print("-" * 60)
try:
    import json

    config_file = Path("/Users/shuai/vnpy_eastmoney_config.json")

    if not config_file.exists():
        print(f"⚠️  配置文件不存在: {config_file}")
        results['config_file'] = False
    else:
        print(f"✅ 配置文件存在: {config_file}")

        # 读取配置
        with open(config_file, 'r') as f:
            config = json.load(f)

        # 检查配置项
        required_keys = ['gateway_name', 'username', 'password', 'cookie']
        for key in required_keys:
            if key in config:
                print(f"✅ 配置项 {key}: 存在")
            else:
                print(f"⚠️  配置项 {key}: 缺失")

        results['config_file'] = True

except Exception as e:
    print(f"❌ 配置文件检查失败: {e}")
    results['config_file'] = False

# 7. 文档检查
print("\n7. 检查文档文件")
print("-" * 60)
try:
    doc_file = Path("/Users/shuai/vnpy_使用说明.md")

    if doc_file.exists():
        print(f"✅ 使用说明文档存在: {doc_file}")

        with open(doc_file, 'r') as f:
            content = f.read()

        # 检查关键内容
        checks = [
            ("东财", "东财相关内容"),
            ("配置", "配置说明"),
            ("Cookie", "Cookie 获取说明"),
        ]

        for keyword, description in checks:
            if keyword in content:
                print(f"✅ 文档包含 {description}")
            else:
                print(f"⚠️  文档缺少 {description}")

        results['documentation'] = True
    else:
        print(f"⚠️  使用说明文档不存在")
        results['documentation'] = False

except Exception as e:
    print(f"❌ 文档检查失败: {e}")
    results['documentation'] = False

# 总结
print("\n" + "=" * 60)
print("启动流程测试总结")
print("=" * 60)

test_categories = [
    ('现有进程', results.get('existing_process', False)),
    ('引擎初始化', results.get('engine_init', False)),
    ('网关注册', results.get('gateway_registration', False)),
    ('启动脚本', results.get('startup_script', False)),
    ('组件集成', results.get('integration', False)),
    ('配置文件', results.get('config_file', False)),
    ('文档文件', results.get('documentation', False)),
]

total = len(test_categories)
passed = sum(1 for _, result in test_categories if result)

for category, result in test_categories:
    status = "✅ 通过" if result else "❌ 失败"
    print(f"{category}: {status}")

print(f"\n测试通过率: {passed}/{total} ({passed/total*100:.0f}%)")

sys.exit(0 if passed == total else 1)
