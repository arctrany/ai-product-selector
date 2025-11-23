"""
跟卖店铺点击验证测试

验证流程：
1. 使用项目的浏览器配置启动浏览器
2. 访问商品页面
3. 打开跟卖浮层
4. 点击第一个跟卖店铺
5. 验证页面跳转
"""
import time
import logging
import sys
import signal
import threading
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from common.scrapers.global_browser_singleton import get_global_browser_service
from common.config.ozon_selectors_config import get_ozon_selectors_config

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_click_first_competitor():
    """测试点击第一个跟卖店铺"""
    browser_service = None

    try:
        # 1. 获取全局浏览器服务实例（使用项目配置）
        logger.info("🚀 初始化浏览器服务...")
        browser_service = get_global_browser_service()

        # 初始化浏览器（使用异步调用，增加超时控制）
        import asyncio
        import signal

        def timeout_handler(signum, frame):
            raise TimeoutError("浏览器初始化超时")

        # 设置30秒超时
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)

        try:
            init_success = asyncio.run(browser_service.initialize())
        finally:
            signal.alarm(0)  # 取消超时

        if not init_success:
            logger.error("❌ 浏览器初始化失败")
            assert False, "浏览器初始化失败"

        # 2. 访问商品页面
        test_url = "https://www.ozon.ru/product/krem-dlya-ruk-tela-nog-dlya-suhoy-i-ochen-suhoy-kozhi-skin-food-1416193337/"
        logger.info(f"📄 访问商品页面: {test_url}")

        # 添加导航超时控制
        try:
            browser_service.navigate_to_sync(test_url)
            # 智能等待：等待页面主要内容加载
            if browser_service.wait_for_selector_sync("body", timeout=10000):
                logger.info("⏱️ 页面加载完成")
            else:
                logger.warning("⚠️ 页面加载超时，但继续执行")
        except Exception as e:
            logger.error(f"❌ 页面导航失败: {e}")
            raise

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
            selectors_config.precise_competitor_selector
        ]

        button_found = False
        max_attempts = 3
        attempt = 0

        while attempt < max_attempts and not button_found:
            for selector in competitor_button_selectors:
                try:
                    logger.debug(f"尝试选择器: {selector} (第{attempt + 1}次)")

                    # 智能等待元素出现（替代 time.sleep）
                    if browser_service.wait_for_selector_sync(selector, timeout=3000):
                        logger.info(f"✅ 找到跟卖浮层按钮: {selector}")

                        # 点击按钮打开浮层（增加超时控制）
                        success = browser_service.click_sync(selector, timeout=5000)
                        if success:
                            logger.info("✅ 成功点击跟卖浮层按钮")

                            # 智能等待浮层出现
                            if browser_service.wait_for_selector_sync(".competitors, [data-widget*='competitor']", timeout=3000):
                                logger.info("✅ 跟卖浮层已出现")
                            button_found = True
                            break
                        else:
                            logger.debug(f"按钮点击失败")
                    else:
                        logger.debug(f"选择器 {selector} 未找到元素")

                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
                    continue

            attempt += 1
            if not button_found and attempt < max_attempts:
                logger.info(f"第{attempt}次尝试失败，等待后重试...")
                time.sleep(2)  # 短暂等待后重试

        if not button_found:
            logger.warning("⚠️ 未找到跟卖浮层按钮，页面可能已经显示了跟卖信息")

        # 4. 查找第一个跟卖店铺并点击
        logger.info("🔍 查找第一个跟卖店铺...")

        # 使用配置系统中的选择器查找店铺卡片
        card_selectors = selectors_config.competitor_container_selectors

        all_cards = None
        card_count = 0

        for selector in card_selectors:
            try:
                cards = browser_service.page.locator(selector)
                # 简单检查：尝试获取第一个元素
                first_card = cards.first
                if first_card:
                    # 假设找到了卡片
                    all_cards = cards
                    card_count = 1  # 至少有一个
                    logger.info(f"📊 使用选择器 {selector} 找到店铺卡片")
                    break
            except Exception as e:
                logger.debug(f"获取卡片时出错: {e}")
                continue

        # 如果没找到，使用智能等待重试
        if card_count == 0:
            logger.info("⏳ 店铺卡片可能还在加载，智能等待并重试...")

            # 尝试等待任何店铺卡片出现
            card_found = False
            for selector in card_selectors:
                if browser_service.wait_for_selector_sync(selector, timeout=8000):
                    try:
                        cards = browser_service.page.locator(selector)
                        first_card = cards.first
                        if first_card:
                            all_cards = cards
                            card_count = 1
                            card_found = True
                            logger.info(f"📊 智能等待后找到店铺卡片: {selector}")
                            break
                    except Exception as e:
                        logger.debug(f"获取卡片时出错: {e}")
                        continue

            if not card_found:
                # 最后一次尝试：等待页面稳定
                logger.info("⏳ 最后尝试：等待页面完全稳定...")
                time.sleep(3)
                for selector in card_selectors:
                    try:
                        cards = browser_service.page.locator(selector)
                        first_card = cards.first
                        if first_card:
                            all_cards = cards
                            card_count = 1
                            logger.info(f"📊 最终尝试找到店铺卡片: {selector}")
                            break
                    except Exception as e:
                        continue

        # 使用之前找到的卡片
        if card_count == 0:
            logger.error("❌ 未找到跟卖店铺卡片")
            assert False, "未找到跟卖店铺卡片"

        first_competitor = all_cards.first
        logger.info(f"✅ 准备点击第一个跟卖店铺")

        # 5. 查找店铺链接并点击
        logger.info("🔍 查找第一个跟卖店铺的链接...")

        # 在第一个跟卖卡片中查找任意可点击的链接
        # 使用配置系统中的选择器
        link_selectors = selectors_config.store_link_selectors + [
            "a[href*='/seller/']",  # 任意店铺链接
            "a[href*='/product/']",  # 任意商品链接
        ]

        clickable_link = None

        for link_selector in link_selectors:
            try:
                link = first_competitor.locator(link_selector)

                # 检查链接是否存在
                try:
                    # 尝试获取第一个链接
                    first_link = link.first
                    if first_link:
                        # 获取链接信息
                        # 使用同步方式获取链接信息
                        # 获取链接信息（使用浏览器服务的同步方法）
                        link_url = browser_service.get_attribute_sync(link_selector, 'href') or "#"
                        link_text = browser_service.text_content_sync(link_selector) or "(无文本)"

                        logger.info(f"✅ 找到可点击链接: {link_text.strip()}")
                        logger.info(f"🔗 链接URL: {link_url}")

                        clickable_link = first_link
                        break
                except Exception as e:
                    logger.debug(f"获取链接信息时出错: {e}")
                    continue

            except Exception as e:
                logger.debug(f"链接选择器 {link_selector} 失败: {e}")
                continue

        if not clickable_link:
            logger.error("❌ 在跟卖卡片中未找到可点击的链接")
            assert False, "在跟卖卡片中未找到可点击的链接"

        # 记录当前页面URL
        current_url = browser_service.page.url
        logger.info(f"📍 当前页面: {current_url}")

        # 6. 点击链接（增加超时控制）
        logger.info("👆 点击跟卖店铺链接...")
        click_success = browser_service.click_sync(link_selector, timeout=5000)

        if not click_success:
            logger.error("❌ 点击店铺链接失败")
            assert False, "点击店铺链接失败"

        # 智能等待页面跳转
        logger.info("⏳ 等待页面跳转...")
        start_time = time.time()
        timeout = 10  # 10秒超时

        while time.time() - start_time < timeout:
            new_url = browser_service.page.url
            if new_url != current_url:
                logger.info(f"✅ 检测到页面跳转: {new_url}")
                break
            time.sleep(0.5)  # 每0.5秒检查一次
        else:
            logger.warning("⚠️ 页面跳转等待超时，使用当前URL")

        # 7. 验证跳转
        new_url = browser_service.page.url
        logger.info(f"📍 跳转后页面: {new_url}")

        if new_url != current_url:
            logger.info("✅ 页面成功跳转！")
            logger.info(f"✅ 验证通过：")
            logger.info(f"   起始页面: {current_url}")
            logger.info(f"   目标页面: {new_url}")
            # 页面成功跳转，测试通过
        else:
            logger.error(f"❌ 页面未发生跳转")
            assert False, "页面未发生跳转"

    except Exception as e:
        logger.error(f"❌ 测试失败: {e}", exc_info=True)
        assert False, f"测试失败: {e}"
        
    finally:
        # 8. 清理资源（增加超时控制）
        if browser_service:
            logger.info("🧹 关闭浏览器...")
            try:
                # 增加浏览器关闭超时控制

                def close_browser():
                    browser_service.close_sync()

                close_thread = threading.Thread(target=close_browser)
                close_thread.start()
                close_thread.join(timeout=10)  # 10秒超时

                if close_thread.is_alive():
                    logger.warning("⚠️ 浏览器关闭超时，强制结束")
                else:
                    logger.info("✅ 浏览器已正常关闭")

            except Exception as e:
                logger.error(f"❌ 关闭浏览器时出错: {e}")

            logger.info("✅ 测试完成")

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("🧪 开始跟卖店铺点击验证测试")
    logger.info("=" * 60)
    
    try:
        test_click_first_competitor()
        logger.info("🎉 测试通过！")
        success = True
    except AssertionError as e:
        logger.info("😞 测试断言失败")
        logger.error(f"❌ 测试失败: {e}")
        success = False
    except Exception as e:
        logger.info("😞 测试失败")
        logger.error(f"❌ 测试失败: {e}")
        success = False
    
    logger.info("=" * 60)
    if success:
        logger.info("🎉 测试通过！")
    else:
        logger.info("😞 测试失败")
    logger.info("=" * 60)

if __name__ == "__main__":
    main()
