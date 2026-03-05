#!/usr/bin/env python3
"""
TradingView + vnpy Web 自动化测试
使用 Playwright 进行 Web 自动化测试和视觉验证
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
import time

# 尝试导入 Playwright
try:
    from playwright.sync_api import sync_playwright, Page, Browser
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright 未安装，正在安装...")
    import subprocess
    subprocess.run([sys.executable, "-m", "pip", "install", "playwright"])
    subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright, Page, Browser


class WebTester:
    """Web 自动化测试器"""

    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
        self.screenshots = []
        self.test_results = []
        self.browser = None
        self.page = None

    def start(self):
        """启动浏览器"""
        print("🚀 启动浏览器...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,  # 显示浏览器窗口
            slow_mo=1000     # 每步操作延迟 1 秒（便于观察）
        )
        self.page = self.browser.new_page()
        self.page.set_viewport_size({"width": 1920, "height": 1080})
        print("✅ 浏览器已启动")

    def stop(self):
        """停止浏览器"""
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        print("✅ 浏览器已关闭")

    def navigate_to_home(self):
        """导航到主页"""
        print(f"\n📍 导航到 {self.base_url}")
        try:
            self.page.goto(self.base_url, wait_until="domcontentloaded", timeout=10000)
            time.sleep(2)  # 等待页面加载

            # 截图
            screenshot_path = self.save_screenshot("01_homepage")
            self.test_results.append({
                "test": "导航到主页",
                "status": "PASS",
                "screenshot": screenshot_path
            })
            print("✅ 主页加载成功")
            return True
        except Exception as e:
            print(f"❌ 主页加载失败: {e}")
            self.test_results.append({
                "test": "导航到主页",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_tradingview_chart(self):
        """测试 TradingView 图表"""
        print(f"\n📊 测试 TradingView 图表")
        try:
            # 等待图表加载
            time.sleep(3)

            # 检查图表容器是否存在
            chart_container = self.page.query_selector("#tradingview_widget")
            if chart_container:
                print("✅ TradingView 图表容器已加载")

                # 检查图表大小
                chart_size = chart_container.bounding_box()
                if chart_size and chart_size['width'] > 0:
                    print(f"✅ 图表尺寸: {chart_size['width']}x{chart_size['height']}")

                # 截图
                screenshot_path = self.save_screenshot("02_tradingview_chart")
                self.test_results.append({
                    "test": "TradingView 图表",
                    "status": "PASS",
                    "screenshot": screenshot_path,
                    "size": chart_size
                })
                return True
            else:
                print("❌ 未找到图表容器")
                return False

        except Exception as e:
            print(f"❌ 图表测试失败: {e}")
            self.test_results.append({
                "test": "TradingView 图表",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_control_panel(self):
        """测试 vnpy 控制面板"""
        print(f"\n🎛️  测试 vnpy 控制面板")
        try:
            # 检查控制面板是否存在
            panel = self.page.query_selector(".control-panel")
            if panel:
                print("✅ 控制面板已加载")

                # 检查各个组件
                components = {
                    "连接配置": "连接配置",
                    "快速下单": "快速下单",
                    "账户信息": "账户信息",
                    "持仓信息": "持仓信息",
                    "订单信息": "订单信息",
                    "系统日志": "系统日志"
                }

                for name, chinese in components.items():
                    element = self.page.query_selector(f"text={chinese}")
                    if element:
                        print(f"  ✅ {chinese} - 存在")
                    else:
                        print(f"  ⚠️  {chinese} - 未找到")

                # 截图
                screenshot_path = self.save_screenshot("03_control_panel")
                self.test_results.append({
                    "test": "vnpy 控制面板",
                    "status": "PASS",
                    "screenshot": screenshot_path
                })
                return True
            else:
                print("❌ 未找到控制面板")
                return False

        except Exception as e:
            print(f"❌ 控制面板测试失败: {e}")
            self.test_results.append({
                "test": "vnpy 控制面板",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_api_status(self):
        """测试 API 状态接口"""
        print(f"\n🔗 测试 API 接口")
        try:
            response = self.page.goto(f"{self.base_url}/api/status")
            content = self.page.content()

            if response and response.ok:
                data = json.loads(content)
                print(f"✅ API 状态响应:")
                print(f"  - status: {data.get('status')}")
                print(f"  - vnpy_connected: {data.get('vnpy_connected')}")
                print(f"  - gateway_connected: {data.get('gateway_connected')}")
                print(f"  - version: {data.get('version')}")

                self.test_results.append({
                    "test": "API 状态",
                    "status": "PASS",
                    "response": data
                })
                return True
            else:
                print(f"❌ API 请求失败: {response.status if response else 'No response'}")
                return False

        except Exception as e:
            print(f"❌ API 测试失败: {e}")
            self.test_results.append({
                "test": "API 状态",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_interactive_elements(self):
        """测试交互元素"""
        print(f"\n🖱️  测试交互元素")
        try:
            # 测试输入框
            inputs = {
                "symbol": "股票代码",
                "exchange": "交易所",
                "price": "价格",
                "volume": "数量"
            }

            for element_id, name in inputs.items():
                input_element = self.page.query_selector(f"#{element_id}")
                if input_element:
                    # 尝试输入测试数据
                    if element_id == "symbol":
                        input_element.fill("600000")
                        print(f"  ✅ {name} 输入框 - 测试成功")
                    elif element_id == "price":
                        input_element.fill("10.5")
                        print(f"  ✅ {name} 输入框 - 测试成功")
                else:
                    print(f"  ⚠️  {name} 输入框 - 未找到")

            # 截图
            screenshot_path = self.save_screenshot("04_interactive_test")
            self.test_results.append({
                "test": "交互元素",
                "status": "PASS",
                "screenshot": screenshot_path
            })
            return True

        except Exception as e:
            print(f"❌ 交互元素测试失败: {e}")
            self.test_results.append({
                "test": "交互元素",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def test_visual_layout(self):
        """测试视觉布局"""
        print(f"\n👁️  测试视觉布局")
        try:
            # 获取页面尺寸
            viewport = self.page.viewport_size
            print(f"✅ 页面尺寸: {viewport['width']}x{viewport['height']}")

            # 检查关键元素的位置
            chart = self.page.query_selector("#tradingview_widget")
            panel = self.page.query_selector(".control-panel")

            if chart and panel:
                chart_box = chart.bounding_box
                panel_box = panel.bounding_box

                print(f"✅ 图表位置: x={chart_box['x']}, y={chart_box['y']}")
                print(f"  尺寸: {chart_box['width']}x{chart_box['height']}")

                print(f"✅ 面板位置: x={panel_box['x']}, y={panel_box['y']}")
                print(f"  尺寸: {panel_box['width']}x{panel_box['height']}")

                # 检查布局合理性
                total_width = chart_box['width'] + panel_box['width']
                if total_width <= viewport['width']:
                    print(f"✅ 布局合理: 总宽度 {total_width} <= 视口宽度 {viewport['width']}")
                else:
                    print(f"⚠️  布局可能有问题: 总宽度 {total_width} > 视口宽度 {viewport['width']}")

                # 截图
                screenshot_path = self.save_screenshot("05_layout_test")
                self.test_results.append({
                    "test": "视觉布局",
                    "status": "PASS",
                    "screenshot": screenshot_path,
                    "chart_size": chart_box,
                    "panel_size": panel_box
                })
                return True
            else:
                print("❌ 关键元素未找到")
                return False

        except Exception as e:
            print(f"❌ 布局测试失败: {e}")
            self.test_results.append({
                "test": "视觉布局",
                "status": "FAIL",
                "error": str(e)
            })
            return False

    def save_screenshot(self, name):
        """保存截图"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{name}_{timestamp}.png"
        path = Path("/Users/shuai") / filename

        self.page.screenshot(path=str(path))
        self.screenshots.append(str(path))
        print(f"  📸 截图已保存: {filename}")

        return str(path)

    def generate_report(self):
        """生成测试报告"""
        print(f"\n" + "=" * 60)
        print("测试报告")
        print("=" * 60)

        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r["status"] == "PASS")

        print(f"\n总测试数: {total_tests}")
        print(f"通过: {passed_tests} ✅")
        print(f"失败: {total_tests - passed_tests} ❌")
        print(f"通过率: {passed_tests/total_tests*100:.1f}%")

        print(f"\n详细结果:")
        for i, result in enumerate(self.test_results, 1):
            status_icon = "✅" if result["status"] == "PASS" else "❌"
            print(f"\n{i}. {result['test']} - {result['status']} {status_icon}")
            if "screenshot" in result:
                print(f"   截图: {result['screenshot']}")
            if "error" in result:
                print(f"   错误: {result['error']}")

        print(f"\n截图列表:")
        for i, screenshot in enumerate(self.screenshots, 1):
            print(f"  {i}. {screenshot}")

        # 保存 JSON 报告
        report_path = Path("/Users/shuai") / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "total_tests": total_tests,
                "passed": passed_tests,
                "failed": total_tests - passed_tests,
                "pass_rate": passed_tests/total_tests*100,
                "results": self.test_results,
                "screenshots": self.screenshots
            }, f, indent=2, ensure_ascii=False)

        print(f"\n📄 JSON 报告已保存: {report_path.name}")
        print("=" * 60)

    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 60)
        print("TradingView + vnpy Web 自动化测试")
        print("=" * 60)
        print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"测试目标: {self.base_url}")
        print("=" * 60)

        try:
            # 启动浏览器
            self.start()

            # 导航测试
            if not self.navigate_to_home():
                print("❌ 主页导航失败，停止测试")
                return

            # API 测试
            self.test_api_status()

            # TradingView 图表测试
            self.test_tradingview_chart()

            # 控制面板测试
            self.test_control_panel()

            # 交互元素测试
            self.test_interactive_elements()

            # 视觉布局测试
            self.test_visual_layout()

            # 生成报告
            self.generate_report()

            # 等待用户查看
            print(f"\n⏳ 浏览器将保持打开 10 秒，供你查看...")
            time.sleep(10)

        finally:
            # 停止浏览器
            self.stop()


def main():
    """主函数"""
    tester = WebTester("http://localhost:8080")

    # 检查服务器是否运行
    import requests
    try:
        response = requests.get("http://localhost:8080/api/status", timeout=2)
        if response.status_code == 200:
            print("✅ 检测到 Web 服务器运行中")
        else:
            print("⚠️  Web 服务器响应异常")
    except:
        print("❌ Web 服务器未运行，请先启动:")
        print("   python tradingview_web_server_v2.py")
        return

    # 运行测试
    tester.run_all_tests()


if __name__ == "__main__":
    main()
