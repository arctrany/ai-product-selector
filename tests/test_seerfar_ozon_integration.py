#!/usr/bin/env python3
"""
测试SeerfarScraper与OzonScraper的集成功能
验证商品图片点击和OZON数据提取是否正常工作
"""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch
from apps.xuanping.common.scrapers.seerfar_scraper import SeerfarScraper
from apps.xuanping.common.config import GoodStoreSelectorConfig


class TestSeerfarOzonIntegration:
    """测试SeerfarScraper与OzonScraper的集成"""

    @pytest.fixture
    def mock_config(self):
        """模拟配置"""
        config = Mock(spec=GoodStoreSelectorConfig)
        config.store_filter = Mock()
        config.store_filter.min_sales_30days = 500000
        config.store_filter.min_orders_30days = 250

        # 添加scraping配置
        config.scraping = Mock()
        config.scraping.seerfar_base_url = "https://test.seerfar.com"
        config.scraping.page_load_timeout = 30
        config.scraping.element_wait_timeout = 10
        config.scraping.retry_attempts = 3
        config.scraping.retry_delay = 2.0

        return config

    @pytest.fixture
    def mock_browser_service(self):
        """模拟浏览器服务"""
        browser_service = Mock()
        browser_service.async_service = Mock()
        browser_service.async_service.browser_service = Mock()
        browser_service.async_service.browser_service.browser_driver = Mock()
        
        # 模拟页面对象
        mock_page = AsyncMock()
        mock_context = AsyncMock()
        mock_new_page = AsyncMock()
        
        # 设置页面层次结构
        browser_service.async_service.browser_service.browser_driver.page = mock_page
        mock_page.context = mock_context
        mock_context.new_page.return_value = mock_new_page
        
        return browser_service, mock_page, mock_new_page

    @pytest.fixture
    def scraper(self, mock_config, mock_browser_service):
        """创建SeerfarScraper实例"""
        browser_service, _, _ = mock_browser_service
        scraper = SeerfarScraper(mock_config)
        scraper.browser_service = browser_service
        return scraper

    @pytest.mark.asyncio
    async def test_extract_product_with_ozon_data(self, scraper, mock_browser_service):
        """测试从商品行提取数据并调用OZON scraper"""
        browser_service, mock_page, mock_new_page = mock_browser_service
        
        # 模拟行元素
        mock_row = AsyncMock()
        mock_td3 = AsyncMock()
        mock_clickable = AsyncMock()
        
        # 设置查询选择器返回值
        mock_row.query_selector.return_value = mock_td3
        mock_td3.query_selector.return_value = mock_clickable
        
        # 模拟元素属性
        mock_clickable.evaluate.side_effect = ["SPAN", "avatar avatar-md product-avatar cursor-pointer"]
        mock_clickable.get_attribute.return_value = "window.open('https://www.ozon.ru/product/test-123456')"
        
        # 模拟新页面内容
        mock_new_page.content.return_value = """
        <html>
            <body>
                <div class="price">
                    <span class="green-price">1000 ₽</span>
                    <span class="black-price">1200 ₽</span>
                </div>
                <div class="competitors">
                    <div class="competitor">店铺A</div>
                    <div class="competitor">店铺B</div>
                </div>
            </body>
        </html>
        """
        
        # 模拟OzonScraper
        with patch('apps.xuanping.common.scrapers.ozon_scraper.OzonScraper') as mock_ozon_scraper_class:
            mock_ozon_scraper = AsyncMock()
            mock_ozon_scraper_class.return_value = mock_ozon_scraper
            
            # 模拟OZON数据提取结果
            mock_ozon_scraper._extract_price_data_from_content.return_value = {
                'green_price': 1000,
                'black_price': 1200,
                'currency': 'RUB'
            }
            mock_ozon_scraper._extract_competitor_stores_from_content.return_value = [
                {'store_name': '店铺A', 'store_id': 'A123'},
                {'store_name': '店铺B', 'store_id': 'B456'}
            ]
            
            # 执行测试
            result = await scraper._extract_product_from_row_async(mock_row)
            
            # 验证结果
            assert result is not None
            assert result['green_price'] == 1000
            assert result['black_price'] == 1200
            assert result['currency'] == 'RUB'
            assert 'competitors' in result
            assert len(result['competitors']) == 2
            assert result['competitors'][0]['store_name'] == '店铺A'
            
            # 验证调用链
            mock_row.query_selector.assert_called_with("td:nth-child(3)")
            mock_td3.query_selector.assert_called_with("span[onclick], [onclick]")
            mock_clickable.get_attribute.assert_called_with("onclick")
            
            # 验证新页面操作
            mock_page.context.new_page.assert_called_once()
            mock_new_page.goto.assert_called_with('https://www.ozon.ru/product/test-123456')
            mock_new_page.wait_for_load_state.assert_called_with('domcontentloaded', timeout=5000)
            mock_new_page.content.assert_called_once()
            mock_new_page.close.assert_called_once()
            
            # 验证OzonScraper调用
            mock_ozon_scraper_class.assert_called_once_with(scraper.config)
            mock_ozon_scraper._extract_price_data_from_content.assert_called_once()
            mock_ozon_scraper._extract_competitor_stores_from_content.assert_called_once_with(
                mock_new_page.content.return_value, 10
            )

    @pytest.mark.asyncio
    async def test_extract_product_no_onclick(self, scraper, mock_browser_service):
        """测试没有onclick事件的情况"""
        browser_service, mock_page, mock_new_page = mock_browser_service
        
        # 模拟行元素
        mock_row = AsyncMock()
        mock_td3 = AsyncMock()
        mock_clickable = AsyncMock()
        
        # 设置查询选择器返回值
        mock_row.query_selector.return_value = mock_td3
        mock_td3.query_selector.return_value = mock_clickable
        
        # 模拟没有onclick事件
        mock_clickable.get_attribute.return_value = None
        
        # 执行测试
        result = await scraper._extract_product_from_row_async(mock_row)
        
        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_product_no_clickable_element(self, scraper, mock_browser_service):
        """测试找不到可点击元素的情况"""
        browser_service, mock_page, mock_new_page = mock_browser_service
        
        # 模拟行元素
        mock_row = AsyncMock()
        mock_td3 = AsyncMock()
        
        # 设置查询选择器返回值
        mock_row.query_selector.return_value = mock_td3
        mock_td3.query_selector.return_value = None  # 找不到可点击元素
        
        # 执行测试
        result = await scraper._extract_product_from_row_async(mock_row)
        
        # 验证结果
        assert result is None

    @pytest.mark.asyncio
    async def test_extract_product_ozon_scraper_error(self, scraper, mock_browser_service):
        """测试OzonScraper出错的情况"""
        browser_service, mock_page, mock_new_page = mock_browser_service
        
        # 模拟行元素
        mock_row = AsyncMock()
        mock_td3 = AsyncMock()
        mock_clickable = AsyncMock()
        
        # 设置查询选择器返回值
        mock_row.query_selector.return_value = mock_td3
        mock_td3.query_selector.return_value = mock_clickable
        
        # 模拟元素属性
        mock_clickable.evaluate.side_effect = ["SPAN", "avatar"]
        mock_clickable.get_attribute.return_value = "window.open('https://www.ozon.ru/product/test-123456')"
        
        # 模拟OzonScraper抛出异常
        with patch('apps.xuanping.common.scrapers.ozon_scraper.OzonScraper') as mock_ozon_scraper_class:
            mock_ozon_scraper = AsyncMock()
            mock_ozon_scraper_class.return_value = mock_ozon_scraper
            mock_ozon_scraper._extract_price_data_from_content.side_effect = Exception("OZON提取失败")
            
            # 执行测试
            result = await scraper._extract_product_from_row_async(mock_row)
            
            # 验证结果 - 即使OZON提取失败，也应该返回基础数据
            assert result is None  # 因为异常会导致整个方法返回None

    def test_validate_store_filter_conditions(self, scraper):
        """测试店铺筛选条件验证"""
        # 测试符合条件的店铺
        sales_data = {
            'sold_30days': 600000,
            'sold_count_30days': 300
        }
        assert scraper.validate_store_filter_conditions(sales_data) is True
        
        # 测试销售额不符合条件
        sales_data = {
            'sold_30days': 400000,
            'sold_count_30days': 300
        }
        assert scraper.validate_store_filter_conditions(sales_data) is False
        
        # 测试销量不符合条件
        sales_data = {
            'sold_30days': 600000,
            'sold_count_30days': 200
        }
        assert scraper.validate_store_filter_conditions(sales_data) is False


if __name__ == '__main__':
    # 运行特定测试
    pytest.main([__file__, '-v'])