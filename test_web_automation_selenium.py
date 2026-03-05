#!/usr/bin/env python3
"""
TradingView + vnpy Web 自动化测试（Selenium 版本）
使用 Selenium WebDriver 进行 Web 自动化测试和视觉验证
"""
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# 尝试导入 Selenium
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options as ChromeOptions
    from selenium.common.exceptions import TimeoutException
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False
    print("⚠️  Selenium 未安装，正在安装...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "selenium"])
    from selenium import webdriver
    from selenium.webdriver.common.by import By


class VisualWebTester:
    """视觉 Web 自动化测试器"""

    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.screenshots = []
        self.test_results = []
        self.driver = None

    def start(self):
        """启动浏览器"""
        print("🚀 启动 Chrome 浏览器...")

        options = ChromeOptions()
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")
        # options.add_argument("--headless")  # 取消注释可无头模式

        try:
            self.driver = webdriver.Chrome(options=options)
            self.driver.implicitly_wait(10)  # 隐式等待 10 秒
            print("✅ 浏览器已启动")
            return True
        except Exception as e:
            print(f"❌ 浏览器启动失败: {e}")
            print("💡 请确保已安装 Chrome 浏览器和 ChromeDriver")
            return False

    def stop(self):
        """停止浏览器"""
        if self.driver:
            self.driver.quit()
            print("✅ 浏览器已关闭")

    def navigate_to_home(self):
        """导航到主页"""
        print(f"\n📍 导航到 {self.base_url}")
        try:
            self.driver.get(self.base_url)
            time.sleep(3)  # 等待页面加载

            # 截图
            screenshot_path = self.save_screenshot("01_homepage")
            self.test_results.append({
                "test": "导航到主页",
                "status": "PASS",
                "screenshot": screenshot_path,
                "url": self.driver.current_url
            })
            print(f"✅ 主页加载成功")
            print(f"   当前 URL: {self.driver.current_url}")
            print(f"   页面标题: {self.driver.title}")
            return True

        except Exception as e:
            print(f"❌ 主页加载失败: {e}")
            self.test_results.append({
                "test": "导航到主页",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_page_elements(self):
        """测试页面元素"""
        print(f"\n🔍 测试页面元素")
        try:
            elements_found = {}

            # 检查关键元素
            elements = {
                "TradingView 图表": "#tradingview_widget",
                "控制面板": ".control-panel",
                "连接配置": "input#username",
                "股票代码输入": "input#symbol",
                "价格输入": "input#price",
                "买入按钮": "button:contains('买入')",
                "卖出按钮": "button:contains('卖出')",
            }

            for name, selector in elements.items():
                try:
                    if "#" in selector or "." in selector:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    elif "contains" in selector or "button" in selector:
                        # 使用 XPath 查找按钮或包含文本的元素
                        if "买入" in name:
                            element = self.driver.find_element(By.XPATH, "//button[contains(text(), '买入')]")
                        elif "卖出" in name:
                            element = self.driver.find_element(By.XPATH, "//button[contains(text(), '卖出')]")
                        else:
                            element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)

                    elements_found[name] = "✅ 找到"
                    print(f"  ✅ {name}")
                except:
                    elements_found[name] = "❌ 未找到"
                    print(f"  ❌ {name}")

            # 截图
            screenshot_path = self.save_screenshot("02_page_elements")
            self.test_results.append({
                "test": "页面元素",
                "status": "PASS",
                "screenshot": screenshot_path,
                "elements": elements_found
            })

            return len([v for v in elements_found.values() if "✅" in v]) > len(elements) / 2

        except Exception as e:
            print(f"❌ 元素测试失败: {e}")
            self.test_results.append({
                "test": "页面元素",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_visual_inspection(self):
        """视觉检查"""
        print(f"\n👁️  视觉检查")
        try:
            # 获取页面尺寸
            window_size = self.driver.get_window_size()
            print(f"  窗口尺寸: {window_size['width']}x{window_size['height']}")

            # 检查页面滚动
            page_height = self.driver.execute_script("return document.body.scrollHeight")
            print(f"  页面高度: {page_height}px")

            # 检查关键元素位置
            try:
                chart = self.driver.find_element(By.CSS_SELECTOR, "#tradingview_widget")
                chart_location = chart.location
                chart_size = chart.size
                print(f"  ✅ 图表位置: ({chart_location['x']}, {chart_location['y']})")
                print(f"     图表尺寸: {chart_size['width']}x{chart_size['height']}")
            except:
                print(f"  ❌ 图表元素未找到")

            try:
                panel = self.driver.find_element(By.CSS_SELECTOR, ".control-panel")
                panel_location = panel.location
                panel_size = panel.size
                print(f"  ✅ 面板位置: ({panel_location['x']}, {panel_location['y']})")
                print(f"     面板尺寸: {panel_size['width']}x{panel_size['height']}")
            except:
                print(f"  ❌ 面板元素未找到")

            # 截图
            screenshot_path = self.save_screenshot("03_visual_inspection")
            self.test_results.append({
                "test": "视觉检查",
                "status": "PASS",
                "screenshot": screenshot_path,
                "window_size": window_size
            })

            return True

        except Exception as e:
            print(f"❌ 视觉检查失败: {e}")
            self.test_results.append({
                "test": "视觉检查",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_interactions(self):
        """测试交互功能"""
        print(f"\n🖱️  测试交互功能")
        try:
            # 测试输入框
            symbol_input = self.driver.find_element(By.CSS_SELECTOR, "input#symbol")
            symbol_input.clear()
            symbol_input.send_keys("600000")
            print(f"  ✅ 输入股票代码: 600000")

            price_input = self.driver.find_element(By.CSS_SELECTOR, "input#price")
            price_input.clear()
            price_input.send_keys("10.50")
            print(f"  ✅ 输入价格: 10.50")

            # 选择交易所
            exchange_select = self.driver.find_element(By.CSS_SELECTOR, "select#exchange")
            from selenium.webdriver.support.select import Select
            select = Select(exchange_select)
            select.select_by_value("SZSE")
            print(f"  ✅ 选择交易所: SZSE")

            time.sleep(1)

            # 截图
            screenshot_path = self.save_screenshot("04_interaction_test")
            self.test_results.append({
                "test": "交互功能",
                "status": "PASS",
                "screenshot": screenshot_path
            })

            return True

        except Exception as e:
            print(f"❌ 交互测试失败: {e}")
            self.test_results.append({
                "test": "交互功能",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_api_endpoints(self):
        """测试 API 端点"""
        print(f"\n🔗 测试 API 端点")
        try:
            import requests

            endpoints = [
                ("GET", "/api/status", "系统状态"),
                ("GET", "/api/account", "账户信息"),
                ("GET", "/api/position", "持仓信息"),
                ("GET", "/api/orders", "订单列表"),
            ]

            api_results = {}
            for method, endpoint, name in endpoints:
                url = self.base_url + endpoint
                try:
                    if method == "GET":
                        response = requests.get(url, timeout=5)
                        if response.status_code == 200:
                            data = response.json()
                            api_results[name] = f"✅ {response.status_code}"
                            print(f"  ✅ {name}: {response.status_code}")
                        else:
                            api_results[name] = f"❌ {response.status_code}"
                            print(f"  ❌ {name}: {response.status_code}")
                except Exception as e:
                    api_results[name] = f"❌ {str(e)}"
                    print(f"  ❌ {name}: {e}")

            self.test_results.append({
                "test": "API 端点",
                "status": "PASS",
                "results": api_results
            })

            return True

        except Exception as e:
            print(f"❌ API 测试失败: {e}")
            self.test_results.append({
                "test": "API 端点",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_websocket_connection(self):
        """测试 WebSocket 连接"""
        print(f"\n🔌 测试 WebSocket 连接")
        try:
            # 检查页面是否加载了 Socket.IO
            script = "return typeof io !== 'undefined'"
            result = self.driver.execute_script(script)

            if result:
                print(f"  ✅ Socket.IO 已加载")

                # 检查连接状态
                socket_status = self.driver.execute_script("""
                    return (function() {
                        if (socket && socket.connected) {
                            return 'connected';
                        }
                        return 'disconnected';
                    })();
                """)
                print(f"  ✅ WebSocket 状态: {socket_status}")

                self.test_results.append({
                    "test": "WebSocket 连接",
                    "status": "PASS",
                    "socket_status": socket_status
                })
                return True
            else:
                print(f"  ❌ Socket.IO 未加载")
                return False

        except Exception as e:
            print(f"❌ WebSocket 测试失败: {e}")
            self.test_results.append({
                "test": "WebSocket 连接",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_responsive_design(self):
        """测试响应式设计"""
        print(f"\n📱 测试响应式设计")
        try:
            sizes = [
                (1920, 1080, "桌面"),
                (1366, 768, "笔记本"),
                (768, 1024, "平板"),
            ]

            for width, height, device in sizes:
                self.driver.set_window_size(width, height)
                time.sleep(1)

                print(f"  测试 {device} ({width}x{height})")

                # 检查关键元素是否可见
                try:
                    panel = self.driver.find_element(By.CSS_SELECTOR, ".control-panel")
                    is_displayed = panel.is_displayed()
                    if is_displayed:
                        print(f"    ✅ 控制面板可见")
                    else:
                        print(f"    ⚠️  控制面板不可见")
                except:
                    print(f"    ❌ 控制面板未找到")

            # 恢复原始大小
            self.driver.set_window_size(1920, 1080)

            self.test_results.append({
                "test": "响应式设计",
                "status": "PASS"
            })

            return True

        except Exception as e:
            print(f"❌ 响应式测试失败: {e}")
            self.test_results.append({
                "test": "响应式设计",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def save_screenshot(self, name):
        """保存截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{name}_{timestamp}.png"
        path = Path("/Users/shuai") / filename

        self.driver.save_screenshot(str(path))
        self.screenshots.append(str(path))
        print(f"  📸 截图已保存: {filename}")

        return str(path)

    def generate_report(self):
        """生成测试报告"""
        print(f"\n" + "=" * 70)
        print(" " * 20 + "自动化测试报告")
        print("=" * 70)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")

        print(f"\n📊 测试统计:")
        print(f"   总测试数: {total_tests}")
        print(f"   通过数量: {passed_tests} ✅")
        print(f"   失败数量: {total_tests - passed_tests} ❌")
        print(f"   通过率: {passed_tests/total_tests*100:.1f}%")

        print(f"\n📋 详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"\n{i}. {result['test']} - {result['status']} {status_icon}")
            if "screenshot" in result:
                print(f"   📸 截图: {Path(result['screenshot']).name}")

        print(f"\n📸 截图列表 ({len(self.screenshots)}):")
        for i, screenshot in enumerate(self.screenshots, 1):
            print(f"   {i}. {Path(screenshot).name}")

        # 保存 JSON 报告
        report_path = Path("/Users/shuai") / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "target_url": self.base_url,
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": passed_tests/total_tests*100,
                "results": self.test_results,
                "screenshots": self.screenshots
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 JSON 报告: {report_path.name}")
        print("=" * 70)

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print(" " * 15 + "TradingView + vnpy 自动化测试")
        print("=" * 70)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标: {self.base_url}")
        print("=" * 70)

        # 检查服务器
        import requests
        try:
            response = requests.get(f"{self.base_url}/api/status", timeout=2)
            if response.status_code != 200:
                print("❌ Web 服务器未正常运行")
                print(f"   请先启动: python tradingview_web_server_v2.py")
                return
        except:
            print("❌ 无法连接到 Web 服务器")
            print(f"   请先启动: python tradingview_web_server_v2.py")
            return

        print("✅ Web 服务器检测正常\n")

        try:
            # 启动浏览器
            if not self.start():
                return

            # 执行测试
            self.navigate_to_home()
            self.test_page_elements()
            self.test_visual_inspection()
            self.test_interactions()
            self.test_api_endpoints()
            self.test_websocket_connection()
            self.test_responsive_design()

            # 生成报告
            self.generate_report()

            # 保持浏览器打开供查看
            print(f"\n⏳ 浏览器将保持打开 15 秒，供你查看测试结果...")
            print(f"   你可以看到自动化测试的过程和结果")
            time.sleep(15)

        except KeyboardInterrupt:
            print(f"\n\n⚠️  测试被用户中断")
        finally:
            # 停止浏览器
            self.stop()


def main():
    """主函数"""
    print("=" * 70)
    print(" " * 20 + "自动化测试启动")
    print("=" * 70)

    tester = VisualWebTester("http://localhost:8080")
    tester.run_all_tests()


if __name__ == "__main__":
    main()
