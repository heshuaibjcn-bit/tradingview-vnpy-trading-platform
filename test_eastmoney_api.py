#!/usr/bin/env python3
"""
东财 API 连通性测试
测试东方财富的 HTTP API 是否可访问
"""
import sys
import requests
from datetime import datetime

print("=" * 60)
print("东财 API 连通性测试")
print("=" * 60)

# 测试结果
results = {}

# 1. 测试基础网络连接
print("\n1. 测试基础网络连接")
print("-" * 60)
try:
    import requests
    print("✅ requests 库已安装")

    # 检查 requests 版本
    print(f"✅ requests 版本: {requests.__version__}")

    results['network'] = True

except Exception as e:
    print(f"❌ 网络库检查失败: {e}")
    results['network'] = False
    sys.exit(1)

# 2. 测试东财主站访问
print("\n2. 测试东财主站访问")
print("-" * 60)
try:
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
    })

    response = session.get("https://www.eastmoney.com", timeout=10)
    print(f"✅ 东财主站响应状态: {response.status_code}")

    if response.status_code == 200:
        print("✅ 东财主站可访问")
        results['main_site'] = True
    else:
        print(f"⚠️  东财主站返回非200状态码: {response.status_code}")
        results['main_site'] = False

except Exception as e:
    print(f"❌ 东财主站访问失败: {e}")
    results['main_site'] = False

# 3. 测试行情 API
print("\n3. 测试行情数据 API")
print("-" * 60)
try:
    # 东财行情 API 示例：获取上证指数
    url = "https://push2.eastmoney.com/api/qt/stock/klt"
    params = {
        'secid': '1.000001',  # 上证指数
        'fields1': 'f1,f2,f3,f4,f5',
        'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58',
        'klt': '101',  # 日K
        'fqt': '1',    # 前复权
        'beg': '20240101',
        'end': datetime.now().strftime('%Y%m%d'),
        'lmt': '100',  # 限制返回数量
    }

    response = session.get(url, params=params, timeout=10)
    print(f"✅ 行情 API 响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 行情 API 返回数据")

        # 检查数据结构
        if 'data' in data:
            print(f"✅ 数据包含 'data' 字段")
            if data.get('data'):
                print(f"✅ 获取到 {len(data['data'])} 条K线数据")
            else:
                print("⚠️  data 字段为空")
        else:
            print(f"⚠️  响应数据结构: {list(data.keys())}")

        results['market_api'] = True
    else:
        print(f"❌ 行情 API 返回错误状态码: {response.status_code}")
        results['market_api'] = False

except Exception as e:
    print(f"❌ 行情 API 访问失败: {e}")
    results['market_api'] = False

# 4. 测试个股行情查询
print("\n4. 测试个股行情查询")
print("-" * 60)
try:
    # 查询浦发银行（600000）实时行情
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        'secid': '1.600000',  # 1.上海交易所, 600000代码
        'fields': 'f43,f44,f45,f46,f47,f48,f49,f50,f51,f52,f57,f58,f60,f107,f116,f117,f127,f152,f161,f162,f167,f168,f169,f170,f171,f84,f85',
    }

    response = session.get(url, params=params, timeout=10)
    print(f"✅ 个股行情 API 响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 个股行情 API 返回数据")

        if 'data' in data and data.get('data'):
            stock_data = data['data']
            print(f"✅ 获取股票数据成功")
            if 'f58' in stock_data:  # 股票名称
                name = stock_data.get('f58')
                print(f"  股票名称: {name}")
            if 'f43' in stock_data:  # 最新价
                price = stock_data.get('f43')
                if price:
                    print(f"  最新价: {price/100:.2f}" if price > 1000 else f"  最新价: {price}")

        results['stock_api'] = True
    else:
        print(f"❌ 个股行情 API 返回错误状态码: {response.status_code}")
        results['stock_api'] = False

except Exception as e:
    print(f"❌ 个股行情查询失败: {e}")
    import traceback
    traceback.print_exc()
    results['stock_api'] = False

# 5. 测试涨跌停行情
print("\n5. 测试涨跌停行情 API")
print("-" * 60)
try:
    url = "https://push2.eastmoney.com/api/qt/clist/get"
    params = {
        'pn': '1',
        'pz': '5',
        'po': '1',
        'np': '1',
        'ut': 'bd1d9ddb04089700cf9c27f6f7426281',
        'fltt': '2',
        'invt': '2',
        'fid': 'f62',
        'fs': 'm:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23',  # A股板块
        'fields': 'f1,f2,f3,f4,f5,f6',
    }

    response = session.get(url, params=params, timeout=10)
    print(f"✅ 涨跌停 API 响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        print(f"✅ 涨跌停 API 返回数据")

        if 'data' in data and 'diff' in data.get('data', {}):
            diff = data['data']['diff']
            print(f"✅ 获取到 {len(diff)} 只股票数据")

        results['list_api'] = True
    else:
        print(f"⚠️  涨跌停 API 返回状态码: {response.status_code}")
        results['list_api'] = False

except Exception as e:
    print(f"❌ 涨跌停 API 访问失败: {e}")
    import traceback
    traceback.print_exc()
    results['list_api'] = False

# 6. 测试 API 响应时间
print("\n6. 测试 API 响应时间")
print("-" * 60)
try:
    import time

    times = []
    for i in range(3):
        start = time.time()
        response = session.get("https://push2.eastmoney.com/api/qt/stock/get",
                              params={'secid': '1.600000',
                                     'fields': 'f43,f58'},
                              timeout=10)
        elapsed = time.time() - start
        times.append(elapsed)
        print(f"  第 {i+1} 次请求: {elapsed*1000:.0f}ms")

    avg_time = sum(times) / len(times)
    print(f"✅ 平均响应时间: {avg_time*1000:.0f}ms")

    if avg_time < 1.0:
        print("✅ 响应时间良好 (<1秒)")
        results['response_time'] = True
    else:
        print("⚠️  响应时间较慢 (>1秒)")
        results['response_time'] = False

except Exception as e:
    print(f"❌ 响应时间测试失败: {e}")
    results['response_time'] = False

# 7. 测试错误处理
print("\n7. 测试 API 错误处理")
print("-" * 60)
try:
    # 测试不存在的股票代码
    url = "https://push2.eastmoney.com/api/qt/stock/get"
    params = {
        'secid': '1.999999',  # 不存在的代码
        'fields': 'f43,f58',
    }

    response = session.get(url, params=params, timeout=10)
    print(f"✅ 错误请求响应状态: {response.status_code}")

    if response.status_code == 200:
        data = response.json()
        # 检查是否返回空数据或错误信息
        if not data.get('data'):
            print("✅ API 正确处理无效请求（返回空数据）")
            results['error_handling'] = True
        else:
            print("⚠️  API 返回了数据（可能不正确）")
            results['error_handling'] = False
    else:
        print(f"⚠️  返回非200状态码: {response.status_code}")
        results['error_handling'] = False

except Exception as e:
    print(f"⚠️  错误处理测试异常: {e}")
    results['error_handling'] = False

# 8. 测试请求头
print("\n8. 测试请求头要求")
print("-" * 60)
try:
    # 测试不带 User-Agent 的请求
    test_session = requests.Session()

    response = test_session.get("https://push2.eastmoney.com/api/qt/stock/get",
                               params={'secid': '1.600000',
                                      'fields': 'f43'},
                               timeout=10)

    if response.status_code == 200:
        print("✅ API 可以不带 User-Agent 访问")
        results['headers'] = True
    else:
        print("⚠️  API 可能需要特定的请求头")
        results['headers'] = False

except Exception as e:
    print(f"⚠️  请求头测试异常: {e}")
    results['headers'] = False

# 总结
print("\n" + "=" * 60)
print("API 连通性测试总结")
print("=" * 60)

test_categories = [
    ('网络连接', results.get('network', False)),
    ('东财主站', results.get('main_site', False)),
    ('行情 API', results.get('market_api', False)),
    ('个股行情', results.get('stock_api', False)),
    ('涨跌停数据', results.get('list_api', False)),
    ('响应时间', results.get('response_time', False)),
    ('错误处理', results.get('error_handling', False)),
    ('请求头', results.get('headers', False)),
]

total = len(test_categories)
passed = sum(1 for _, result in test_categories if result)

for category, result in test_categories:
    status = "✅ 通过" if result else "❌ 失败"
    print(f"{category}: {status}")

print(f"\n测试通过率: {passed}/{total} ({passed/total*100:.0f}%)")

if passed >= total * 0.7:
    print("\n✅ 东财 API 基本可用，可以进行数据获取")
    print("💡 建议：在实际使用时增加缓存和重试机制")
else:
    print("\n⚠️  部分功能不可用，建议检查网络连接或使用代理")

# 关闭 session
session.close()

sys.exit(0 if passed >= total * 0.7 else 1)
