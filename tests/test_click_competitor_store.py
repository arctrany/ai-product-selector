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
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.scrapers.global_browser_singleton import get_global_browser_service
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
        # 1. 获取全局浏览器服务实例（使用项目配置）
        logger.info("🚀 初始化浏览器服务...")
        browser_service = get_global_browser_service()

        # 初始化浏览器
        init_success = await browser_service.initialize()
        if not init_success:
            logger.error("❌ 浏览器初始化失败")
            return False
        
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
        else:
            # 等待浮层容器出现
            logger.info("⏳ 等待跟卖浮层加载...")
            try:
                # 等待浮层容器出现
                await browser_service.page.wait_for_selector("div.pdp_b2k", state='visible', timeout=10000)
                logger.info("✅ 跟卖浮层已加载")
            except Exception as e:
                logger.warning(f"⚠️ 等待浮层超时: {e}")

        # 4. 查找第一个跟卖店铺并点击
        logger.info("🔍 查找第一个跟卖店铺...")

        # 尝试新旧两种选择器查找店铺卡片
        card_selectors = [
            "div.pdp_bk3",  # 新版选择器
            "div.pdp_kb2",  # 旧版选择器
        ]

        all_cards = None
        card_count = 0
        used_selector = None

        for selector in card_selectors:
            cards = browser_service.page.locator(selector)
            count = await cards.count()
            if count > 0:
                all_cards = cards
                card_count = count
                used_selector = selector
                logger.info(f"📊 使用选择器 {selector} 找到 {card_count} 个店铺卡片")
                break

        # 如果没找到，等待更长时间并重试
        if card_count == 0:
            logger.info("⏳ 店铺卡片可能还在加载，等待5秒后重试...")
            await asyncio.sleep(5)

            for selector in card_selectors:
                cards = browser_service.page.locator(selector)
                count = await cards.count()
                if count > 0:
                    all_cards = cards
                    card_count = count
                    used_selector = selector
                    logger.info(f"📊 重试后使用 {selector} 找到 {card_count} 个店铺卡片")
                    break

        # 如果还是0，保存HTML用于调试
        if card_count == 0:
            logger.warning("⚠️ 仍未找到店铺卡片，保存页面HTML用于调试...")
            html_content = await browser_service.page.content()
            debug_file = "tests/resources/debug-click-test.html"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.info(f"📄 HTML已保存到: {debug_file}")

            # 同时截图
            screenshot_file = "tests/resources/debug-click-test.png"
            await browser_service.page.screenshot(path=screenshot_file, full_page=True)
            logger.info(f"📸 截图已保存到: {screenshot_file}")

        # 使用之前找到的卡片
        if card_count == 0:
            logger.error("❌ 未找到跟卖店铺卡片")
            return False

        first_competitor = all_cards.first
        logger.info(f"✅ 准备点击第一个跟卖店铺")
        
        # 5. 查找店铺链接并点击
        logger.info("🔍 查找第一个跟卖店铺的链接...")
        
        # 在第一个跟卖卡片中查找任意可点击的链接
        link_selectors = [
            # 新版选择器
            "a.pdp_a5e",  # 店铺名称链接
            "a.pdp_e2a",  # Logo链接
            # 旧版选择器
            "a.pdp_ae5",  # 店铺名称链接
            "a.pdp_ea2",  # Logo链接
            # 通用选择器
            "a[href*='/seller/']",  # 任意店铺链接
            "a[href*='/product/']",  # 任意商品链接
        ]

        clickable_link = None

        for link_selector in link_selectors:
            try:
                link = first_competitor.locator(link_selector)

                if await link.count() > 0:
                    # 获取链接信息
                    link_url = await link.first.get_attribute('href')
                    link_text = await link.first.text_content() or "(无文本)"

                    logger.info(f"✅ 找到可点击链接: {link_text.strip()}")
                    logger.info(f"🔗 链接URL: {link_url}")

                    clickable_link = link.first
                    break

            except Exception as e:
                logger.debug(f"链接选择器 {link_selector} 失败: {e}")
                continue

        if not clickable_link:
            logger.error("❌ 在跟卖卡片中未找到可点击的链接")
            return False
        
        # 记录当前页面URL
        current_url = browser_service.page.url
        logger.info(f"📍 当前页面: {current_url}")
        
        # 6. 点击链接
        logger.info("👆 点击跟卖店铺链接...")
        await clickable_link.click()

        # 等待页面跳转
        logger.info("⏳ 等待页面跳转...")
        await asyncio.sleep(3)

        # 7. 验证跳转
        new_url = browser_service.page.url
        logger.info(f"📍 跳转后页面: {new_url}")

        if new_url != current_url:
            logger.info("✅ 页面成功跳转！")
            logger.info(f"✅ 验证通过：")
            logger.info(f"   起始页面: {current_url}")
            logger.info(f"   目标页面: {new_url}")
            return True
        else:
            logger.error(f"❌ 页面未发生跳转")
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
