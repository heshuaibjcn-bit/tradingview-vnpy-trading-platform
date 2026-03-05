#!/usr/bin/env python3
"""
东财网关代码质量检查
验证语法、接口完整性、类型提示等
"""
import sys
import ast
import inspect
from pathlib import Path

print("=" * 60)
print("东财网关代码质量检查")
print("=" * 60)

# 测试结果
results = {}

# 1. 语法检查
print("\n1. Python 语法检查")
print("-" * 60)
try:
    gateway_file = Path("/Users/shuai/vnpy_gateway_eastmoney.py")
    with open(gateway_file, 'r', encoding='utf-8') as f:
        code = f.read()
    ast.parse(code)
    print("✅ Python 语法正确")
    results['syntax'] = True
except SyntaxError as e:
    print(f"❌ 语法错误: {e}")
    results['syntax'] = False

# 2. 导入网关类
print("\n2. 类定义检查")
print("-" * 60)
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from vnpy_gateway_eastmoney import EastmoneyGateway
    print(f"✅ EastmoneyGateway 类导入成功")

    # 检查类继承
    from vnpy.trader.gateway import BaseGateway
    if issubclass(EastmoneyGateway, BaseGateway):
        print(f"✅ 正确继承 BaseGateway")
        results['inheritance'] = True
    else:
        print(f"❌ 未正确继承 BaseGateway")
        results['inheritance'] = False
except Exception as e:
    print(f"❌ 类导入失败: {e}")
    results['inheritance'] = False

# 3. 必需方法检查
print("\n3. BaseGateway 必需方法检查")
print("-" * 60)

required_methods = [
    'connect',
    'close',
    'subscribe',
    'send_order',
    'cancel_order',
    'query_account',
    'query_position',
]

method_results = {}
for method_name in required_methods:
    if hasattr(EastmoneyGateway, method_name):
        method = getattr(EastmoneyGateway, method_name)
        if callable(method):
            print(f"✅ {method_name}()")
            method_results[method_name] = True
        else:
            print(f"❌ {method_name} 不是方法")
            method_results[method_name] = False
    else:
        print(f"❌ 缺少 {method_name}")
        method_results[method_name] = False

results['required_methods'] = all(method_results.values())

# 4. 可选方法检查
print("\n4. 可选方法检查")
print("-" * 60)

optional_methods = [
    'query_history',
    'send_quote',
    'cancel_quote',
]

optional_results = {}
for method_name in optional_methods:
    if hasattr(EastmoneyGateway, method_name):
        method = getattr(EastmoneyGateway, method_name)
        if callable(method):
            print(f"✅ {method_name}() (已实现)")
            optional_results[method_name] = True
        else:
            print(f"⚠️  {method_name} 不是方法")
            optional_results[method_name] = False
    else:
        print(f"⚠️  {method_name} (未实现)")
        optional_results[method_name] = False

results['optional_methods'] = optional_results

# 5. 类属性检查
print("\n5. 类属性检查")
print("-" * 60)

required_attributes = [
    ('default_name', str),
    ('exchanges', list),
]

attribute_results = {}
for attr_name, attr_type in required_attributes:
    if hasattr(EastmoneyGateway, attr_name):
        attr_value = getattr(EastmoneyGateway, attr_name)
        if isinstance(attr_value, attr_type):
            print(f"✅ {attr_name}: {type(attr_value).__name__}")
            attribute_results[attr_name] = True
        else:
            print(f"❌ {attr_name} 类型错误，期望 {attr_type.__name__}")
            attribute_results[attr_name] = False
    else:
        print(f"❌ 缺少属性 {attr_name}")
        attribute_results[attr_name] = False

results['attributes'] = all(attribute_results.values())

# 6. 方法签名检查
print("\n6. 关键方法签名检查")
print("-" * 60)

signature_tests = [
    ('connect', ['self', 'setting']),
    ('close', ['self']),
    ('subscribe', ['self', 'req']),
    ('send_order', ['self', 'req']),
    ('cancel_order', ['self', 'req']),
]

signature_results = {}
for method_name, expected_params in signature_tests:
    if hasattr(EastmoneyGateway, method_name):
        method = getattr(EastmoneyGateway, method_name)
        sig = inspect.signature(method)
        actual_params = list(sig.parameters.keys())

        if actual_params == expected_params:
            print(f"✅ {method_name}({', '.join(expected_params)})")
            signature_results[method_name] = True
        else:
            print(f"❌ {method_name} 参数不匹配")
            print(f"   期望: {expected_params}")
            print(f"   实际: {actual_params}")
            signature_results[method_name] = False
    else:
        print(f"❌ 缺少方法 {method_name}")
        signature_results[method_name] = False

results['signatures'] = all(signature_results.values())

# 7. 类型提示检查
print("\n7. 类型提示检查")
print("-" * 60)

type_hints_results = {}
for method_name in ['connect', 'send_order']:
    if hasattr(EastmoneyGateway, method_name):
        method = getattr(EastmoneyGateway, method_name)
        sig = inspect.signature(method)
        has_hints = any(v.annotation != inspect.Parameter.empty
                       for v in sig.parameters.values())

        if has_hints:
            print(f"✅ {method_name} 有类型提示")
            type_hints_results[method_name] = True
        else:
            print(f"⚠️  {method_name} 缺少类型提示")
            type_hints_results[method_name] = False

results['type_hints'] = any(type_hints_results.values())

# 8. 文档字符串检查
print("\n8. 文档字符串检查")
print("-" * 60)

doc_results = {}
# 检查类文档
if EastmoneyGateway.__doc__:
    print(f"✅ EastmoneyGateway 类有文档字符串")
    doc_results['class'] = True
else:
    print(f"⚠️  EastmoneyGateway 类缺少文档字符串")
    doc_results['class'] = False

# 检查方法文档
for method_name in ['connect', 'send_order']:
    if hasattr(EastmoneyGateway, method_name):
        method = getattr(EastmoneyGateway, method_name)
        if method.__doc__:
            print(f"✅ {method_name} 方法有文档字符串")
            doc_results[method_name] = True
        else:
            print(f"⚠️  {method_name} 方法缺少文档字符串")
            doc_results[method_name] = False

results['docstrings'] = all(doc_results.values())

# 总结
print("\n" + "=" * 60)
print("代码质量检查总结")
print("=" * 60)

categories = [
    ('语法检查', results.get('syntax', False)),
    ('继承关系', results.get('inheritance', False)),
    ('必需方法', results.get('required_methods', False)),
    ('类属性', results.get('attributes', False)),
    ('方法签名', results.get('signatures', False)),
]

total = len(categories)
passed = sum(1 for _, result in categories if result)

for category, result in categories:
    status = "✅ 通过" if result else "❌ 失败"
    print(f"{category}: {status}")

print(f"\n总体评分: {passed}/{total} 项通过")
print(f"代码质量: {passed/total*100:.0f}%")

sys.exit(0 if passed == total else 1)
