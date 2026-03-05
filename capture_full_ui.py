#!/usr/bin/env python3
"""
捕获完整TradingView界面截图
"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def capture_full_ui(url="http://localhost:8080", output_path="/tmp/trading_full_ui.png"):
    """捕获完整TradingView界面截图"""
    print(f"正在访问: {url}")

    chrome_options = Options()
    chrome_options.add_argument('--headless')  # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')

    driver = webdriver.Chrome(options=chrome_options)

    try:
        # 访问页面
        driver.get(url)

        # 等待TradingView加载（需要更长时间）
        print("等待TradingView加载...")
        time.sleep(15)

        # 等待TradingView widget容器加载
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.ID, "tradingview_widget"))
            )
            print("✅ TradingView容器加载完成")
        except:
            print("⚠️  TradingView容器未找到")

        # 再等待一会儿让Widget完全加载
        time.sleep(5)

        # 截图
        driver.save_screenshot(output_path)
        print(f"✅ 截图已保存: {output_path}")

        # 获取页面标题
        title = driver.title
        print(f"页面标题: {title}")

        # 检查关键元素
        elements_to_check = {
            "TradingView容器": "#tradingview_widget",
            "插件按钮": ".plugin-toggle",
            "插件面板": "#tradingPlugin",
            "连接状态": ".status-indicator"
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

        # 检查页面内容
        print("\n页面内容检查:")
        has_widget = "TradingView.widget" in driver.page_source
        has_plugin = "量化交易系统" in driver.page_source
        print(f"  TradingView Widget: {'✅' if has_widget else '❌'}")
        print(f"  交易插件: {'✅' if has_plugin else '❌'}")

        return True, output_path

    except Exception as e:
        print(f"❌ 截图失败: {str(e)}")
        return False, None

    finally:
        driver.quit()

if __name__ == "__main__":
    success, path = capture_full_ui()

    if success:
        print(f"\n✅ 截图成功完成")
        print(f"文件路径: {path}")
    else:
        print(f"\n❌ 截图失败")
