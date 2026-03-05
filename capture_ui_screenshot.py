#!/usr/bin/env python3
"""
使用Selenium截图并分析界面问题
"""
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_ui_screenshot(url="http://localhost:8080", output_path="/tmp/trading_ui_analysis.png"):
    """截取TradingView界面"""
    print(f"正在访问: {url}")

    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--screenshot=/tmp/screenshot.png')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 访问页面
        driver.get(url)

        # 等待页面加载
        time.sleep(5)

        # 等待关键元素加载
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "main-container"))
            )
            print("✅ 页面主容器加载完成")
        except:
            print("⚠️  页面主容器未找到")

        # 再等待一会儿让JavaScript执行完成
        time.sleep(5)

        # 等待数据加载完成（等待总资产不再是"--"）
        print("\n等待数据加载...")
        max_retries = 20
        for i in range(max_retries):
            try:
                total_assets = driver.execute_script(
                    "return document.getElementById('totalAssets').textContent"
                )
                if total_assets and total_assets != '--':
                    print(f"✅ 数据加载完成 (总资产: {total_assets})")
                    break
                time.sleep(0.5)
            except Exception as e:
                print(f"⚠️  检查数据时出错: {str(e)}")
                time.sleep(0.5)
        else:
            print("⚠️  数据加载超时，继续截图")

        # 额外等待确保视觉渲染完成
        time.sleep(2)

        # 检查JavaScript状态和数据
        print("\nJavaScript执行状态检查:")
        try:
            # 检查localStorage
            token = driver.execute_script("return localStorage.getItem('token')")
            print(f"  Token状态: {'有token' if token else '无token'}")

            # 检查数据元素值
            total_assets = driver.execute_script("return document.getElementById('totalAssets').textContent")
            print(f"  总资产: {total_assets}")

            last_price = driver.execute_script("return document.getElementById('lastPrice').textContent")
            print(f"  最新价: {last_price}")

            # 检查是否有持仓数据
            positions_html = driver.execute_script("return document.getElementById('positionsList').innerHTML")
            has_positions = 'empty-state' not in positions_html
            print(f"  持仓列表: {'有数据' if has_positions else '空'}")

        except Exception as e:
            print(f"  ❌ JavaScript检查失败: {str(e)}")

        # 截图
        driver.save_screenshot(output_path)
        print(f"✅ 截图已保存: {output_path}")

        # 获取页面标题
        title = driver.title
        print(f"页面标题: {title}")

        # 检查关键元素
        elements_to_check = {
            "导航栏": ".navbar",
            "图表容器": "#tradingview_chart",
            "交易面板": ".right-panel",
            "账户信息": ".account-info",
            "登录按钮": "#loginBtn",
            "连接状态": ".connection-status"
        }

        print("\n元素检查:")
        for name, selector in elements_to_check.items():
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"  ✅ {name}: 找到 {len(elements)} 个")
                else:
                    print(f"  ❌ {name}: 未找到")
            except Exception as e:
                print(f"  ❌ {name}: 检查失败 - {str(e)}")

        # 获取控制台错误
        logs = driver.get_log('browser')
        print(f"\n浏览器控制台日志 ({len(logs)} 条):")
        for log in logs:  # 显示所有日志
            print(f"  [{log['level']}] {log['message']}")

        return True, output_path

    except Exception as e:
        print(f"❌ 截图失败: {str(e)}")
        return False, None

    finally:
        driver.quit()

if __name__ == "__main__":
    success, path = capture_ui_screenshot()

    if success:
        print(f"\n✅ 截图成功完成")
        print(f"文件路径: {path}")
        sys.exit(0)
    else:
        print(f"\n❌ 截图失败")
        sys.exit(1)
