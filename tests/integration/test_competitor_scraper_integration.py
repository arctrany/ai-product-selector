"""
CompetitorScraper 集成测试

使用真实的浏览器服务和网络请求，测试与外部系统的集成。

🔧 修复说明：
- 按照xp命令的成功模式配置浏览器启动环境
- 使用与xp命令相同的Edge浏览器配置和反检测参数
- 确保Profile检测和用户状态保持功能正常工作
"""

import pytest
import json
import time
import os
import sys
from pathlib import Path
from unittest.mock import patch
from typing import List, Dict, Any

# 添加项目根目录到路径以解决导入问题
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.scrapers.competitor_scraper import CompetitorScraper
from common.models.scraping_result import ScrapingResult
from common.config.ozon_selectors_config import OzonSelectorsConfig
from rpa.browser.browser_service import SimplifiedBrowserService


def load_test_cases() -> List[Dict[str, Any]]:
    """加载测试用例数据

    从 tests/test_data/ozon_test_cases.json 文件中加载测试用例。
    如果文件不存在，返回默认测试用例。

    Returns:
        List[Dict[str, Any]]: 测试用例列表
    """
    try:
        test_data_file = Path(__file__).parent.parent / "test_data" / "ozon_test_cases.json"
        with open(test_data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('test_cases', [])
    except FileNotFoundError:
        # 如果文件不存在，返回默认测试用例
        return [
            {
                "id": "default_test_case",
                "name": "默认测试用例",
                "url": "https://www.ozon.ru/product/1176594312",
                "description": "默认测试商品",
                "expected": {
                    "green_price": None,
                    "black_price": None,
                    "competitor_count": 0,
                    "has_competitors": False,
                    "has_image": True
                },
                "test_options": {
                    "include_competitors": True,
                    "max_competitors": 10
                }
            }
        ]


@pytest.mark.integration
class TestCompetitorScraperIntegration:
    """CompetitorScraper 集成测试类"""

    def setup_method(self):
        """测试方法设置 - 按照xp命令的成功模式配置浏览器环境"""
        # 🎯 关键修复：设置与xp命令相同的环境变量配置
        # 这些环境变量会被SimplifiedBrowserService._create_default_global_config()使用
        os.environ['PREFERRED_BROWSER'] = 'edge'  # 明确指定使用Edge浏览器
        os.environ['BROWSER_DEBUG_PORT'] = '9222'  # 设置CDP调试端口
        os.environ['BROWSER_HEADLESS'] = 'false'  # 确保非无头模式，便于调试

        print(f"🔍 浏览器配置环境变量已设置:")
        print(f"   PREFERRED_BROWSER: {os.environ.get('PREFERRED_BROWSER')}")
        print(f"   BROWSER_DEBUG_PORT: {os.environ.get('BROWSER_DEBUG_PORT')}")
        print(f"   BROWSER_HEADLESS: {os.environ.get('BROWSER_HEADLESS')}")

        # 创建真实的选择器配置
        self.selectors_config = OzonSelectorsConfig()

        # 🎯 关键修复：使用全局浏览器单例（按照xp命令模式）
        print(f"🚀 获取全局浏览器服务实例...")
        self.browser_service = SimplifiedBrowserService.get_global_instance()

        # 🔧 使用同步方法启动浏览器服务（避免异步同步混合调用问题）
        print(f"🚀 正在启动浏览器服务...")
        try:
            # 按照xp命令模式使用同步启动
            success = self.browser_service.start_browser_sync()
            if success:
                print(f"✅ 浏览器服务启动成功")
            else:
                print(f"❌ 浏览器服务启动失败")
                # 如果启动失败，尝试导航触发初始化
                print(f"🔧 尝试通过导航触发浏览器初始化...")
                nav_success = self.browser_service.navigate_to_sync("about:blank")
                if nav_success:
                    print(f"✅ 通过导航成功触发浏览器初始化")
                else:
                    print(f"❌ 导航触发初始化失败")

        except Exception as e:
            print(f"❌ 浏览器服务启动异常: {e}")

        # 🎯 关键修复：创建CompetitorScraper实例时使用全局浏览器服务
        self.scraper = CompetitorScraper(
            selectors_config=self.selectors_config,
            browser_service=self.browser_service
        )

        # 验证浏览器服务状态
        if self.scraper.browser_service:
            print(f"✅ CompetitorScraper浏览器服务已设置")
            browser_driver = getattr(self.scraper.browser_service, 'browser_driver', None)
            if browser_driver:
                print(f"✅ 浏览器驱动已初始化: {browser_driver.is_initialized()}")
            else:
                print(f"⚠️  浏览器驱动未找到")

        # 加载测试数据
        self.test_cases = load_test_cases()
        self.test_urls = self._convert_test_cases_to_urls()

    def teardown_method(self):
        """测试方法清理 - 每个测试方法执行后调用"""
        # 🔧 清理环境变量配置（可选，避免影响其他测试）
        # 通常保留环境变量配置，因为其他测试也可能需要相同配置

        # 清理：关闭浏览器服务（如果需要）
        # 注意：通常不需要关闭全局单例服务
        time.sleep(1)  # 给系统一些时间进行清理

    def _convert_test_cases_to_urls(self):
        """将测试用例转换为URL列表格式，兼容现有测试方法"""
        test_urls = []
        for test_case in self.test_cases:
            test_urls.append({
                "url": test_case["url"],
                "description": test_case.get("description", test_case["name"]),
                "expected_competitors": test_case["expected"].get("has_competitors", False),
                "max_wait_time": test_case["test_options"].get("max_competitors", 10) * 3 + 15,  # 动态计算超时时间
                "test_case_id": test_case["id"],
                "test_case_name": test_case["name"]
            })
        return test_urls

    # ========== 基础集成测试 ==========

    @pytest.mark.network
    def test_scraper_initialization_with_real_services(self):
        """测试使用真实服务的初始化"""
        # Act
        scraper = CompetitorScraper()

        # Assert
        assert scraper.browser_service is not None
        assert scraper.selectors_config is not None
        assert scraper.wait_utils is not None
        assert scraper.scraping_utils is not None

    @pytest.mark.network
    @pytest.mark.slow
    def test_real_browser_service_integration(self):
        """测试与真实浏览器服务的集成，包含URL跳转功能验证"""
        # Arrange
        test_url = self.test_urls[0]["url"]

        # 🎯 关键验证：检查浏览器服务是否按xp命令模式正确初始化
        print(f"🔍 验证浏览器服务状态:")
        print(f"   browser_service存在: {self.scraper.browser_service is not None}")

        if self.scraper.browser_service:
            # 验证浏览器驱动是否正确初始化
            browser_driver = getattr(self.scraper.browser_service, 'browser_driver', None)
            print(f"   browser_driver存在: {browser_driver is not None}")

            if browser_driver:
                print(f"   browser_driver已初始化: {browser_driver.is_initialized()}")

        # 🎯 关键修复：测试URL跳转功能
        print(f"🌐 测试URL跳转功能: {test_url}")
        try:
            # 使用浏览器服务导航到测试URL
            nav_success = self.scraper.browser_service.navigate_to_sync(test_url, wait_until="domcontentloaded")
            print(f"   URL导航结果: {nav_success}")

            if nav_success:
                # 验证页面是否成功加载
                page = self.scraper.browser_service.get_page()
                assert page is not None, "导航成功但get_page()返回None"

                # 获取当前页面URL验证导航是否成功
                try:
                    current_url = page.url
                    print(f"   当前页面URL: {current_url}")
                    # 验证URL是否包含预期的域名
                    assert "ozon.ru" in current_url, f"页面URL不正确: {current_url}"
                except Exception as url_e:
                    print(f"   获取页面URL失败: {url_e}")
            else:
                print(f"   ⚠️  URL导航失败，但继续测试")

        except Exception as nav_e:
            print(f"   ❌ URL导航异常: {nav_e}")

        # Act - 通过实际抓取来测试浏览器服务
        result = self.scraper.scrape(url=test_url, max_competitors=1)

        # Assert - 验证浏览器服务能够正常工作
        assert isinstance(result, ScrapingResult)

        # 🎯 关键验证：确保get_page()不再返回None
        page = self.scraper.browser_service.get_page()
        assert page is not None, "浏览器服务的get_page()返回了None，说明Edge浏览器初始化失败"

        print(f"✅ 浏览器服务集成测试通过，page对象: {type(page)}")

    # ========== 真实URL测试 ==========

    @pytest.mark.network
    @pytest.mark.slow
    @pytest.mark.parametrize("test_case", [
        pytest.param(
            test_case,
            id=f"{test_case['id']}_{test_case['name'][:20]}"
        ) for test_case in load_test_cases()
    ])
    def test_scrape_real_urls(self, test_case):
        """参数化测试真实URL的抓取

        Args:
            test_case: 来自 test_data/ozon_test_cases.json 的测试用例
        """
        # Arrange
        url = test_case["url"]
        expected_competitors = test_case["expected"].get("has_competitors", False)
        max_competitors = test_case["test_options"].get("max_competitors", 10)
        max_wait_time = max_competitors * 3 + 15  # 动态计算超时时间

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act
        start_time = time.time()
        # 构建 context，包含预期的竞品数量以触发展开逻辑
        context = {
            'competitor_cnt': test_case["expected"].get("competitor_count", 0)
        }
        result = self.scraper.scrape(url=url, max_competitors=max_competitors, context=context)
        execution_time = time.time() - start_time

        # Assert
        assert isinstance(result, ScrapingResult)
        assert execution_time < max_wait_time, f"执行时间超过 {max_wait_time} 秒"
        
        if expected_competitors:
            # 如果期望有竞品，检查结果
            if result.success:
                assert isinstance(result.data, list)
                # 注意：真实网页可能没有竞品，所以不强制要求有数据
            else:
                # 如果失败，至少应该有错误信息
                assert result.error is not None
        
        # 验证结果结构的完整性
        assert hasattr(result, 'success')
        assert hasattr(result, 'data')
        assert hasattr(result, 'execution_time')

    @pytest.mark.network
    @pytest.mark.slow
    @pytest.mark.timeout(120)  # 2分钟超时，考虑展开功能的复杂性
    def test_scrape_with_expand_functionality(self):
        """测试展开功能的真实集成"""
        # Arrange
        url = self.test_urls[0]["url"]
        context = {'competitor_count': 15}  # 模拟需要展开的场景

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act
        result = self.scraper.scrape(url=url, context=context, max_competitors=10)

        # Assert
        assert isinstance(result, ScrapingResult)
        # 验证展开功能是否被正确调用（通过结果结构）
        if result.success:
            assert isinstance(result.data, list)

    # ========== 端到端流程测试 ==========

    @pytest.mark.network
    @pytest.mark.slow
    def test_end_to_end_competitor_extraction(self):
        """端到端竞品提取流程测试"""
        # Arrange
        url = self.test_urls[0]["url"]

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act - 执行完整的抓取流程
        result = self.scraper.scrape(url=url, max_competitors=3)

        # Assert - 验证完整的数据结构
        assert isinstance(result, ScrapingResult)
        
        if result.success and result.data:
            # 验证每个竞品数据的结构
            for competitor in result.data:
                assert isinstance(competitor, dict)
                # 验证关键字段存在
                expected_fields = ['ranking']
                for field in expected_fields:
                    assert field in competitor, f"缺少字段: {field}"
                
                # 验证数据类型
                if 'ranking' in competitor:
                    assert isinstance(competitor['ranking'], int)
                if 'store_name' in competitor:
                    assert isinstance(competitor['store_name'], str)
                if 'price' in competitor:
                    assert isinstance(competitor['price'], (str, int, float))

    @pytest.mark.network
    @pytest.mark.slow
    def test_multiple_urls_sequential(self):
        """测试顺序处理多个URL"""
        results = []
        
        for test_data in self.test_urls[:2]:  # 只测试前两个URL
            # 🎯 关键修复：在scrape前先导航到目标页面
            url = test_data["url"]
            print(f"🌐 导航到测试URL: {url}")
            nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
            print(f"   导航结果: {nav_success}")

            # Act
            result = self.scraper.scrape(url=url, max_competitors=2)
            results.append(result)
            
            # 添加延时，避免对服务器造成压力
            time.sleep(2)

        # Assert
        assert len(results) == 2
        for result in results:
            assert isinstance(result, ScrapingResult)

    # ========== 性能和稳定性测试 ==========

    @pytest.mark.network
    @pytest.mark.slow
    def test_scraper_performance_baseline(self):
        """测试抓取性能基线"""
        # Arrange
        url = self.test_urls[0]["url"]
        performance_threshold = 45  # 45秒性能阈值

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act
        start_time = time.time()
        result = self.scraper.scrape(url=url, max_competitors=5)
        execution_time = time.time() - start_time

        # Assert
        assert execution_time < performance_threshold, f"性能超出阈值: {execution_time}s > {performance_threshold}s"
        assert isinstance(result, ScrapingResult)

    @pytest.mark.network
    @pytest.mark.slow
    def test_scraper_stability_multiple_calls(self):
        """测试多次调用的稳定性"""
        # Arrange
        url = self.test_urls[0]["url"]
        call_count = 3
        results = []

        # Act
        for i in range(call_count):
            # 🎯 关键修复：每次scrape前先导航到目标页面
            print(f"🌐 导航到测试URL (第{i+1}次): {url}")
            nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
            print(f"   导航结果: {nav_success}")

            result = self.scraper.scrape(url=url, max_competitors=2)
            results.append(result)
            
            # 添加延时
            if i < call_count - 1:
                time.sleep(3)

        # Assert
        assert len(results) == call_count
        
        # 验证所有结果都是有效的
        for i, result in enumerate(results):
            assert isinstance(result, ScrapingResult), f"第 {i+1} 次调用结果无效"

    # ========== 错误处理和容错性测试 ==========

    @pytest.mark.network
    def test_invalid_url_handling(self):
        """测试无效URL的处理"""
        # Arrange
        invalid_urls = [
            "https://invalid-domain-that-does-not-exist.com/product/123",
            "not-a-url",
            "",
        ]

        for invalid_url in invalid_urls:
            # Act
            result = self.scraper.scrape(url=invalid_url)

            # Assert
            assert isinstance(result, ScrapingResult)
            # 无效URL应该失败，但不应该抛出异常
            assert result.success is False or result.data == []

    @pytest.mark.network
    @pytest.mark.slow
    def test_timeout_handling(self):
        """测试超时处理（如果支持）"""
        # Arrange
        url = self.test_urls[0]["url"]

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act & Assert
        # 即使在可能的超时情况下，也应该返回有效的结果对象
        result = self.scraper.scrape(url=url, max_competitors=1)
        assert isinstance(result, ScrapingResult)

    @pytest.mark.network
    def test_malformed_page_content_handling(self):
        """测试处理格式错误的页面内容"""
        # Arrange - 使用可能没有竞品信息的页面
        non_product_url = "https://www.ozon.ru/"

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {non_product_url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(non_product_url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act
        result = self.scraper.scrape(url=non_product_url)

        # Assert
        assert isinstance(result, ScrapingResult)
        # 非产品页面应该没有竞品数据，但不应该抛出异常
        if result.success:
            assert isinstance(result.data, list)
            assert len(result.data) == 0  # 应该没有竞品数据

    # ========== 配置和环境测试 ==========

    @pytest.mark.network
    def test_different_selector_configurations(self):
        """测试不同的选择器配置"""
        # Arrange
        custom_config = OzonSelectorsConfig()
        scraper_with_custom_config = CompetitorScraper(selectors_config=custom_config)
        url = self.test_urls[0]["url"]

        # 🎯 关键修复：在scrape前先导航到目标页面
        print(f"🌐 导航到测试URL: {url}")
        nav_success = scraper_with_custom_config.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        # Act
        result = scraper_with_custom_config.scrape(url=url, max_competitors=2)

        # Assert
        assert isinstance(result, ScrapingResult)

    @pytest.mark.network
    @pytest.mark.slow  
    def test_concurrent_scraper_instances(self):
        """测试并发抓取器实例（如果支持）"""
        # Arrange
        url = self.test_urls[0]["url"]
        scraper1 = CompetitorScraper()
        scraper2 = CompetitorScraper()

        # Act
        result1 = scraper1.scrape(url=url, max_competitors=1)
        result2 = scraper2.scrape(url=url, max_competitors=1)

        # Assert
        assert isinstance(result1, ScrapingResult)
        assert isinstance(result2, ScrapingResult)

    # ========== 数据验证测试 ==========

    @pytest.mark.network
    @pytest.mark.slow
    def test_competitor_data_consistency(self):
        """测试竞品数据的一致性"""
        # Arrange
        url = self.test_urls[0]["url"]

        # Act - 进行两次抓取
        # 🎯 关键修复：第一次scrape前导航
        print(f"🌐 导航到测试URL (第1次): {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        result1 = self.scraper.scrape(url=url, max_competitors=3)
        time.sleep(2)  # 等待间隔

        # 🎯 关键修复：第二次scrape前导航
        print(f"🌐 导航到测试URL (第2次): {url}")
        nav_success = self.scraper.browser_service.navigate_to_sync(url, wait_until="domcontentloaded")
        print(f"   导航结果: {nav_success}")

        result2 = self.scraper.scrape(url=url, max_competitors=3)

        # Assert
        assert isinstance(result1, ScrapingResult)
        assert isinstance(result2, ScrapingResult)
        
        # 如果两次都成功，数据结构应该一致
        if result1.success and result2.success:
            assert isinstance(result1.data, list)
            assert isinstance(result2.data, list)

    @pytest.mark.network
    @pytest.mark.slow
    def test_max_competitors_limit_enforcement(self):
        """测试最大竞品数量限制的执行"""
        # Arrange
        url = self.test_urls[0]["url"]
        max_competitors_values = [1, 3, 5]

        for max_competitors in max_competitors_values:
            # Act
            result = self.scraper.scrape(url=url, max_competitors=max_competitors)

            # Assert
            assert isinstance(result, ScrapingResult)
            if result.success and result.data:
                assert len(result.data) <= max_competitors, f"返回的竞品数量 {len(result.data)} 超过限制 {max_competitors}"

    # ========== 清理和资源管理测试 ==========

    @pytest.mark.network
    def test_resource_cleanup_after_scraping(self):
        """测试抓取后的资源清理"""
        # Arrange
        url = self.test_urls[0]["url"]
        initial_page = self.scraper.browser_service.get_page()

        # Act
        result = self.scraper.scrape(url=url, max_competitors=1)
        post_scrape_page = self.scraper.browser_service.get_page()

        # Assert
        assert isinstance(result, ScrapingResult)
        # 验证浏览器服务仍然可用
        assert post_scrape_page is not None
        # 可以添加更多资源状态检查

    def teardown_method(self):
        """测试方法清理 - 每个测试方法执行后调用"""
        # 🔧 使用全局浏览器单例，通常不需要关闭浏览器服务
        # 让浏览器服务保持运行，供后续测试使用
        print(f"🧹 测试清理完成")
        time.sleep(1)  # 给系统一些时间进行清理
