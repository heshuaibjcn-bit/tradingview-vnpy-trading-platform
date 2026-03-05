#!/usr/bin/env python3
"""
Dump page state to debug rendering issues
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def dump_page_state(url="http://localhost:8080"):
    """Dump page HTML and element states"""
    print(f"正在访问: {url}")

    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        driver.get(url)
        time.sleep(10)  # Wait for page to load

        # Wait for data to load
        print("\n等待数据加载...")
        for i in range(20):
            total_assets = driver.execute_script(
                "return document.getElementById('totalAssets').textContent"
            )
            if total_assets and total_assets != '--':
                print(f"✅ 数据已加载: {total_assets}")
                break
            time.sleep(0.5)
        else:
            print("⚠️  数据未加载")

        time.sleep(2)  # Extra wait for rendering

        # Dump element states
        print("\n=== 元素状态 ===")
        elements = {
            'totalAssets': '总资产',
            'availableBalance': '可用资金',
            'positionValue': '持仓市值',
            'todayProfit': '今日盈亏',
            'lastPrice': '最新价',
            'priceChange': '涨跌幅',
            'quoteVolume': '成交量',
        }

        for elem_id, name in elements.items():
            try:
                text = driver.execute_script(
                    f"return document.getElementById('{elem_id}')?.textContent || 'NOT FOUND'"
                )
                print(f"  {name} ({elem_id}): {text}")
            except Exception as e:
                print(f"  {name} ({elem_id}): ERROR - {str(e)}")

        # Check price input
        price_value = driver.execute_script(
            "return document.getElementById('price')?.value || 'NOT FOUND'"
        )
        print(f"  价格输入框 (price): {price_value}")

        # Check positions and orders
        print("\n=== 列表状态 ===")
        positions_html = driver.execute_script(
            "return document.getElementById('positionsList')?.innerHTML || 'NOT FOUND'"
        )
        if 'empty-state' in positions_html:
            print("  持仓列表: 空状态")
        elif 'position-item' in positions_html:
            count = positions_html.count('position-item')
            print(f"  持仓列表: {count} 个持仓")
        else:
            print(f"  持仓列表: {positions_html[:100]}...")

        orders_html = driver.execute_script(
            "return document.getElementById('ordersList')?.innerHTML || 'NOT FOUND'"
        )
        if 'empty-state' in orders_html:
            print("  订单列表: 空状态")
        elif 'order-item' in orders_html:
            count = orders_html.count('order-item')
            print(f"  订单列表: {count} 个订单")
        else:
            print(f"  订单列表: {orders_html[:100]}...")

        # Check layout
        print("\n=== 布局状态 ===")
        main_container_width = driver.execute_script(
            "return document.querySelector('.main-container')?.offsetWidth || 'NOT FOUND'"
        )
        chart_width = driver.execute_script(
            "return document.querySelector('.chart-container')?.offsetWidth || 'NOT FOUND'"
        )
        right_panel_width = driver.execute_script(
            "return document.querySelector('.right-panel')?.offsetWidth || 'NOT FOUND'"
        )

        print(f"  主容器宽度: {main_container_width}")
        print(f"  图表容器宽度: {chart_width}")
        print(f"  右侧面板宽度: {right_panel_width}")

        if isinstance(chart_width, (int, float)) and isinstance(right_panel_width, (int, float)):
            total = chart_width + right_panel_width
            chart_pct = (chart_width / total) * 100
            right_pct = (right_panel_width / total) * 100
            print(f"  实际比例: {chart_pct:.1f}% : {right_pct:.1f}%")

        # Check if formatCurrency exists
        format_exists = driver.execute_script(
            "return typeof formatCurrency !== 'undefined'"
        )
        print(f"\n=== 函数状态 ===")
        print(f"  formatCurrency 函数存在: {format_exists}")

    except Exception as e:
        print(f"❌ 错误: {str(e)}")
    finally:
        driver.quit()

if __name__ == "__main__":
    dump_page_state()
