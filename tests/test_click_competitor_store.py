"""
跟卖店铺点击验证测试

验证流程：
1. 使用项目的浏览器配置启动浏览器
2. 访问商品页面
3. 打开跟卖浮层
4. 点击第一个跟卖店铺
5. 验证页面跳转
"""
import asyncio
import logging
from common.scrapers.xuanping_browser_service import XuanpingBrowserService
from common.config.ozon_selectors import get_ozon_selectors_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_click_first_competitor():
    """测试点击第一个跟卖店铺"""
    browser_service = None
    
    try:
        # 1. 初始化浏览器服务（使用项目配置）
        logger.info("🚀 初始化浏览器服务...")
        browser_service = XuanpingBrowserService()
        await browser_service.initialize()
        
        # 2. 访问商品页面
        test_url = "https://www.ozon.ru/product/krem-dlya-ruk-tela-nog-dlya-suhoy-i-ochen-suhoy-kozhi-skin-food-1416193337/"
        logger.info(f"📄 访问商品页面: {test_url}")
        await browser_service.navigate_to(test_url)
        
        # 等待页面加载
        await browser_service.page.wait_for_load_state('networkidle')
        logger.info("✅ 页面加载完成")
        
        # 3. 查找并点击跟卖浮层按钮
        logger.info("🔍 查找跟卖浮层按钮...")
        
        # 获取选择器配置
        selectors_config = get_ozon_selectors_config()
        
        # 尝试多种选择器定位跟卖按钮
        competitor_button_selectors = [
            # 基于HTML结构的选择器
            "button:has-text('Еще')",  # 包含"Еще"文本的按钮
            "button.b25_4_4-a0.b25_4_4-b7",  # 精确类选择器
            "button:has-text('продавцов')",  # 包含"продавцов"的按钮
            "//button[contains(text(), 'Еще')]",  # XPath
            
            # 使用配置的选择器
            selectors_config.PRECISE_COMPETITOR_SELECTOR
        ]
        
        button_found = False
        for selector in competitor_button_selectors:
            try:
                logger.debug(f"尝试选择器: {selector}")
                
                # 判断是否为XPath
                if selector.startswith('//') or selector.startswith('(//'):
                    button = browser_service.page.locator(f"xpath={selector}")
                else:
                    button = browser_service.page.locator(selector)
                
                # 检查元素是否存在
                if await button.count() > 0:
                    logger.info(f"✅ 找到跟卖浮层按钮: {selector}")
                    
                    # 等待按钮可见和可点击
                    await button.first.wait_for(state='visible', timeout=5000)
                    
                    # 点击按钮打开浮层
                    await button.first.click()
                    logger.info("✅ 成功点击跟卖浮层按钮")
                    button_found = True
                    
                    # 等待浮层出现
                    await asyncio.sleep(2)
                    break
                    
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        
        if not button_found:
            logger.warning("⚠️ 未找到跟卖浮层按钮，页面可能已经显示了跟卖信息")
        
        # 4. 查找第一个跟卖店铺并点击
        logger.info("🔍 查找第一个跟卖店铺...")
        
        # 基于HTML结构的选择器
        competitor_card_selectors = [
            "div.pdp_kb2",  # 店铺卡片容器
            "div.pdp_b2k > div.pdp_kb2",  # 完整路径
        ]
        
        first_competitor = None
        for selector in competitor_card_selectors:
            try:
                cards = browser_service.page.locator(selector)
                count = await cards.count()
                
                if count > 0:
                    logger.info(f"✅ 找到 {count} 个跟卖店铺，使用选择器: {selector}")
                    first_competitor = cards.first
                    break
                    
            except Exception as e:
                logger.debug(f"选择器 {selector} 失败: {e}")
                continue
        
        if not first_competitor:
            logger.error("❌ 未找到跟卖店铺")
            return False
        
        # 5. 查找店铺链接并点击
        logger.info("🔍 查找第一个跟卖店铺的链接...")
        
        # 在第一个跟卖卡片中查找链接
        link_selectors = [
            "a.pdp_ae5[href*='/seller/']",  # 精确的店铺链接
            "a[href*='/seller/']",  # 包含seller的链接
            "a.pdp_ae5",  # 店铺链接类
        ]
        
        store_link = None
        store_url = None
        
        for link_selector in link_selectors:
            try:
                link = first_competitor.locator(link_selector)
                
                if await link.count() > 0:
                    # 获取链接URL
                    store_url = await link.first.get_attribute('href')
                    store_name = await link.first.text_content()
                    
                    logger.info(f"✅ 找到店铺链接: {store_name}")
                    logger.info(f"🔗 店铺URL: {store_url}")
                    
                    store_link = link.first
                    break
                    
            except Exception as e:
                logger.debug(f"链接选择器 {link_selector} 失败: {e}")
                continue
        
        if not store_link:
            logger.error("❌ 未找到店铺链接")
            return False
        
        # 记录当前页面URL
        current_url = browser_service.page.url
        logger.info(f"📍 当前页面: {current_url}")
        
        # 6. 点击店铺链接
        logger.info("👆 点击第一个跟卖店铺链接...")
        await store_link.click()
        
        # 等待页面跳转
        await asyncio.sleep(3)
        
        # 7. 验证跳转
        new_url = browser_service.page.url
        logger.info(f"📍 跳转后页面: {new_url}")
        
        if new_url != current_url and '/seller/' in new_url:
            logger.info("✅ 成功跳转到店铺页面！")
            logger.info(f"✅ 验证通过：从 {current_url} 跳转到 {new_url}")
            return True
        else:
            logger.error(f"❌ 页面未跳转或跳转失败")
            return False
            
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        return False
        
    finally:
        # 8. 清理资源
        if browser_service:
            logger.info("🧹 关闭浏览器...")
            await browser_service.close()
            logger.info("✅ 测试完成")


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 开始跟卖店铺点击验证测试")
    logger.info("=" * 60)
    
    success = await test_click_first_competitor()
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 测试通过！")
    else:
        logger.info("😞 测试失败")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
