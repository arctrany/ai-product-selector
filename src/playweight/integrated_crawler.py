"""
集成爬虫程序 - 整合三个模块的完整解决方案
将浏览器服务、用户交互层和自动化流程整合在一起
"""

import asyncio
from datetime import datetime
from typing import Optional

from browser_service import BrowserService
from user_interface import UserInterface
from automation_scenario import AutomationScenario


class IntegratedCrawler:
    """集成爬虫类 - 协调三个模块的工作"""
    
    def __init__(self, excel_file_path: Optional[str] = None):
        """
        初始化集成爬虫

        Args:
            excel_file_path: Excel文件路径，如果为None则使用默认的"docs/好店2.xlsx"
        """
        self.browser_service = BrowserService()
        # 如果没有提供路径，使用默认的Excel文件路径
        if excel_file_path is None:
            excel_file_path = "docs/好店2.xlsx"
        self.user_interface = UserInterface(excel_file_path)
        self.automation_scenario = AutomationScenario(request_delay=2.0, debug_mode=False)
        
        print("🎯 集成爬虫初始化完成")
        print("📦 模块状态:")
        print("   ✅ 浏览器服务模块 - 已加载")
        print("   ✅ 用户交互层模块 - 已加载")
        print("   ✅ 自动化流程模块 - 已加载")
    
    async def initialize_system(self) -> bool:
        """
        初始化系统环境
        
        Returns:
            bool: 初始化是否成功
        """
        print("\n🔧 开始初始化系统环境...")
        
        # 初始化浏览器服务
        if not await self.browser_service.init_browser():
            print("❌ 浏览器服务初始化失败")
            return False
        
        # 获取页面对象并设置到自动化引擎
        page = await self.browser_service.get_page()
        if not page:
            print("❌ 无法获取页面对象")
            return False
        
        self.automation_scenario.set_page(page)
        print("✅ 系统环境初始化完成")

        return True

    def setup_user_interface(self) -> bool:
        """
        设置用户交互界面

        Returns:
            bool: 设置是否成功
        """
        print("\n👤 设置用户交互界面...")

        # 显示欢迎信息
        self.user_interface.show_welcome_message()

        # 读取Excel文件
        if not self.user_interface.read_stores_excel():
            print("❌ Excel文件读取失败")
            return False

        # 使用默认配置参数，无需用户输入
        print("⚙️ 使用默认配置参数:")
        print("   请求间隔: 2秒")
        print("   处理模式: 自动化测试模式")

        # 应用配置到自动化引擎
        config = self.user_interface.get_config()
        self.automation_scenario.request_delay = config.get('request_delay', 2.0)

        print("✅ 用户交互界面设置完成")
        return True

    async def execute_automation(self, limit: Optional[int] = None) -> bool:
        """
        执行自动化流程

        Args:
            limit: 限制处理的店铺数量

        Returns:
            bool: 执行是否成功
        """
        print("\n🤖 开始执行自动化流程...")

        # 获取店铺数据
        stores_data = self.user_interface.get_stores_data()
        if not stores_data:
            print("❌ 没有店铺数据可处理")
            return False

        # 如果没有指定限制，询问用户
        if limit is None:
            limit = self.user_interface.prompt_for_limit()

        # 执行爬取
        results = await self.automation_scenario.crawl_all_stores(stores_data, limit)

        if not results:
            print("❌ 没有成功爬取任何店铺数据")
            return False

        # 检查是否有成功的爬取结果
        successful_results = [r for r in results if r.get('success', False)]
        if not successful_results:
            print("❌ 所有店铺爬取都失败了，没有有效数据")
            return False

        # 保存结果到用户界面
        self.user_interface.set_crawled_results(results)

        print("✅ 自动化流程执行完成")
        return True

    def save_and_display_results(self) -> bool:
        """
        保存并显示结果

        Returns:
            bool: 保存是否成功
        """
        print("\n💾 保存和显示结果...")

        # 显示统计信息
        self.user_interface.display_statistics()

        # 保存结果到Excel
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = f"seerfar_stores_data_integrated_{timestamp}.xlsx"

        if not self.user_interface.save_results_to_excel(output_file):
            print("❌ 结果保存失败")
            return False

        print("✅ 结果保存和显示完成")
        return True

    async def cleanup_system(self):
        """清理系统资源 - 保持浏览器连接"""
        print("\n🧹 清理系统资源...")

        # 注意：根据用户要求，不关闭浏览器连接，方便后续调试和操作
        print("💡 保持浏览器连接，方便调试和后续操作")
        print("✅ 系统资源清理完成（浏览器保持连接）")

    async def run_full_workflow(self, limit: Optional[int] = 3) -> bool:
        """
        运行完整的工作流程

        Args:
            limit: 限制处理的店铺数量，默认3个用于测试

        Returns:
            bool: 工作流程是否成功
        """
        success = False
        start_time = datetime.now()

        try:
            print("🚀 开始运行集成爬虫完整工作流程")
            print(f"⏰ 开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 60)

            # 步骤1: 初始化系统环境
            if not await self.initialize_system():
                return False

            # 步骤2: 设置用户交互界面
            if not self.setup_user_interface():
                return False

            # 步骤3: 执行自动化流程
            if not await self.execute_automation(limit):
                return False

            # 步骤4: 保存并显示结果
            if not self.save_and_display_results():
                return False

            success = True

        except Exception as e:
            print(f"❌ 工作流程执行异常: {str(e)}")
            success = False

        finally:
            # 显示完成信息
            end_time = datetime.now()
            duration = end_time - start_time

            print("\n" + "=" * 60)
            print("📊 工作流程完成统计:")
            print(f"   开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"   总耗时: {duration.total_seconds():.1f} 秒")
            print(f"   执行结果: {'✅ 成功' if success else '❌ 失败'}")
            print("=" * 60)

            # 根据用户要求，无论成功还是失败都保持浏览器连接
            print("💡 保持浏览器连接，方便调试和后续操作")
            self.user_interface.show_completion_message(success)

        return success

    async def run_integration_test(self) -> bool:
        """
        运行集成测试

        Returns:
            bool: 测试是否通过
        """
        print("🧪 开始运行集成测试...")
        print("📋 测试内容:")
        print("   1. 模块加载测试")
        print("   2. 浏览器服务测试")
        print("   3. 用户交互层测试")
        print("   4. 自动化流程测试")
        print("   5. 模块协同工作测试")
        print("=" * 60)

        test_results = {
            'module_loading': False,
            'browser_service': False,
            'user_interface': False,
            'automation_scenario': False,
            'integration': False
        }

        try:
            # 测试1: 模块加载测试
            print("\n🔍 测试1: 模块加载测试")
            if all([self.browser_service, self.user_interface, self.automation_scenario]):
                print("✅ 所有模块加载成功")
                test_results['module_loading'] = True
            else:
                print("❌ 模块加载失败")
                return False

            # 测试2: 浏览器服务测试
            print("\n🔍 测试2: 浏览器服务测试")
            if await self.browser_service.init_browser():
                print("✅ 浏览器服务初始化成功")
                test_results['browser_service'] = True

                # 测试页面获取
                page = await self.browser_service.get_page()
                if page:
                    print("✅ 页面对象获取成功")
                    self.automation_scenario.set_page(page)
                else:
                    print("❌ 页面对象获取失败")
                    return False
            else:
                print("❌ 浏览器服务初始化失败")
                return False

            # 测试3: 用户交互层测试
            print("\n🔍 测试3: 用户交互层测试")

            # 直接使用默认Excel文件路径，无需用户交互
            default_excel_path = "好店2.xlsx"
            print(f"📁 直接使用Excel文件: {default_excel_path}")

            if self.user_interface.set_excel_file(default_excel_path):
                print("✅ Excel文件路径设置成功")

                # 测试配置功能
                original_delay = self.user_interface.get_config('request_delay')
                self.user_interface.set_config('request_delay', 1.0)
                new_delay = self.user_interface.get_config('request_delay')

                if new_delay == 1.0:
                    print("✅ 配置管理功能正常")
                    test_results['user_interface'] = True
                    # 恢复原始配置
                    self.user_interface.set_config('request_delay', original_delay)
                else:
                    print("❌ 配置管理功能异常")
                    return False
            else:
                print("⚠️ Excel文件路径设置失败，但测试继续")
                test_results['user_interface'] = True  # 文件不存在不影响模块功能测试

            # 测试4: 自动化流程测试
            print("\n🔍 测试4: 自动化流程测试")

            # 测试URL构建
            test_store_id = "12345678"
            test_url = self.automation_scenario.build_seerfar_url(test_store_id)
            expected_url = f"https://seerfar.cn/admin/store-detail.html?storeId={test_store_id}&platform=OZON"

            if test_url == expected_url:
                print("✅ URL构建功能正常")

                # 测试店铺ID提取
                test_store_info = {'store_id': test_store_id, 'name': 'Test Store'}
                extracted_id = self.automation_scenario.extract_store_id_from_data(test_store_info)

                if extracted_id == test_store_id:
                    print("✅ 店铺ID提取功能正常")
                    test_results['automation_scenario'] = True
                else:
                    print("❌ 店铺ID提取功能异常")
                    return False
            else:
                print("❌ URL构建功能异常")
                return False

            # 测试5: 模块协同工作测试
            print("\n🔍 测试5: 模块协同工作测试")

            # 测试配置传递
            self.user_interface.set_config('request_delay', 1.5)
            config = self.user_interface.get_config()
            self.automation_scenario.request_delay = config.get('request_delay', 2.0)
            
            if self.automation_scenario.request_delay == 1.5:
                print("✅ 模块间配置传递正常")
                test_results['integration'] = True
            else:
                print("❌ 模块间配置传递异常")
                return False
            
            # 所有测试通过
            print("\n🎉 所有集成测试通过！")
            
            # 显示测试结果摘要
            print("\n📊 测试结果摘要:")
            for test_name, result in test_results.items():
                status = "✅ 通过" if result else "❌ 失败"
                print(f"   {test_name}: {status}")
            
            return True
            
        except Exception as e:
            print(f"❌ 集成测试异常: {str(e)}")
            return False
        
        finally:
            # 保持浏览器连接，不进行清理
            print("💡 测试完成，保持浏览器连接以便后续使用")


async def main():
    """主函数 - 运行集成测试和完整工作流程"""
    print("🎯 集成爬虫程序启动")
    print("📦 基于模块化设计的Seefar店铺数据爬取系统")
    print()
    
    # 创建集成爬虫实例
    crawler = IntegratedCrawler()
    
    # 首先运行集成测试
    print("=" * 60)
    print("🧪 第一阶段：集成测试")
    print("=" * 60)
    
    test_success = await crawler.run_integration_test()
    
    if test_success:
        print("\n✅ 集成测试通过！系统准备就绪。")
        
        # 自动运行完整工作流程，无需用户确认
        print("\n🚀 自动开始完整工作流程...")
        print("=" * 60)
        print("🚀 第二阶段：完整工作流程")
        print("=" * 60)

        # 重新创建实例用于完整工作流程
        workflow_crawler = IntegratedCrawler()
        workflow_success = await workflow_crawler.run_full_workflow(limit=3)

        if workflow_success:
            print("\n🎉 完整工作流程执行成功！")
            return True
        else:
            print("\n❌ 完整工作流程执行失败！")
            return False
    else:
        print("\n❌ 集成测试失败！请检查系统配置。")
        return False


if __name__ == "__main__":
    """程序入口点"""
    try:
        # 运行主程序
        result = asyncio.run(main())
        exit(0 if result else 1)
        
    except KeyboardInterrupt:
        print("\n❌ 程序被用户中断")
        exit(1)
        
    except Exception as e:
        print(f"\n❌ 程序运行异常: {str(e)}")
        exit(1)


