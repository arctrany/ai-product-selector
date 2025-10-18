"""
Seerfar场景实现 - 具体的Seerfar店铺数据爬取场景
整合AutomationScenario和SceneInterface，提供完整的Seerfar爬取功能
"""

import asyncio
from datetime import datetime
from typing import Optional, List, Dict, Any

from .automation_scenario import AutomationScenario
from .scene_interface import SceneInterface

class SeerfarScene:
    """Seerfar场景类 - 整合自动化流程和场景界面"""
    
    def __init__(self, excel_file_path: Optional[str] = None, **config):
        """
        初始化Seerfar场景
        
        Args:
            excel_file_path: Excel文件路径
            **config: 配置参数
        """
        # 初始化场景界面
        self.scene_interface = SceneInterface(excel_file_path)
        
        # 初始化自动化场景，使用配置参数
        self.automation_scenario = AutomationScenario(
            request_delay=config.get('request_delay', 2.0),
            debug_mode=config.get('debug_mode', False),
            max_products_per_store=config.get('max_products_per_store', 21)
        )
        
        print("🎯 Seerfar场景初始化完成")
        print(f"   ⚙️ 请求间隔: {self.automation_scenario.request_delay}秒")
        print(f"   🐛 调试模式: {self.automation_scenario.debug_mode}")
        print(f"   🔢 每店铺最大商品数: {self.automation_scenario.max_products_per_store}")
    
    def set_page(self, page):
        """
        设置页面对象
        
        Args:
            page: Playwright页面对象
        """
        self.automation_scenario.set_page(page)
    
    def setup_data(self) -> bool:
        """
        设置数据源
        
        Returns:
            bool: 设置是否成功
        """
        print("\n📊 设置数据源...")
        
        # 读取Excel文件
        if not self.scene_interface.read_stores_excel():
            print("❌ Excel文件读取失败")
            return False
        
        print("✅ 数据源设置完成")
        return True
    
    async def execute(self, limit: Optional[int] = None) -> bool:
        """
        执行Seerfar场景
        
        Args:
            limit: 限制处理的店铺数量
            
        Returns:
            bool: 执行是否成功
        """
        print("\n🤖 开始执行Seerfar场景...")
        
        # 获取店铺数据
        stores_data = self.scene_interface.get_stores_data()
        if not stores_data:
            print("❌ 没有店铺数据可处理")
            return False
        
        # 如果没有指定限制，使用默认值或询问用户
        if limit is None:
            limit = self.scene_interface.prompt_for_limit()
        
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
        
        # 保存结果到场景界面
        self.scene_interface.set_crawled_results(results)
        
        print("✅ Seerfar场景执行完成")
        return True
    
    def save_results(self, output_file: Optional[str] = None) -> bool:
        """
        保存结果
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            bool: 保存是否成功
        """
        print("\n💾 保存Seerfar场景结果...")
        
        # 显示统计信息
        self.scene_interface.display_statistics()
        
        # 生成输出文件名
        if not output_file:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_file = f"seerfar_stores_data_scene_{timestamp}.xlsx"
        
        # 保存结果到Excel
        if not self.scene_interface.save_results_to_excel(output_file):
            print("❌ 结果保存失败")
            return False
        
        print("✅ Seerfar场景结果保存完成")
        return True
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        results = self.scene_interface.crawled_results
        if not results:
            return {}
        
        successful_count = len([r for r in results if r.get('success')])
        failed_count = len([r for r in results if not r.get('success')])
        total_products = sum(len(r.get('products', [])) for r in results)
        
        return {
            'total_stores': len(results),
            'successful_stores': successful_count,
            'failed_stores': failed_count,
            'success_rate': (successful_count / len(results) * 100) if results else 0,
            'total_products': total_products
        }
    
    async def run_test(self, test_limit: int = 1) -> bool:
        """
        运行场景测试
        
        Args:
            test_limit: 测试店铺数量限制
            
        Returns:
            bool: 测试是否通过
        """
        print(f"🧪 开始运行Seerfar场景测试（限制{test_limit}个店铺）...")
        
        try:
            # 设置数据源
            if not self.setup_data():
                return False
            
            # 执行场景
            if not await self.execute(limit=test_limit):
                return False
            
            # 保存结果
            test_output = f"seerfar_scene_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            if not self.save_results(test_output):
                return False
            
            # 显示测试结果
            stats = self.get_statistics()
            print("\n📊 场景测试结果:")
            print(f"   总店铺数量: {stats.get('total_stores', 0)}")
            print(f"   成功爬取: {stats.get('successful_stores', 0)}")
            print(f"   成功率: {stats.get('success_rate', 0):.1f}%")
            print(f"   总商品数量: {stats.get('total_products', 0)}")
            
            print("✅ Seerfar场景测试通过")
            return True
            
        except Exception as e:
            print(f"❌ Seerfar场景测试异常: {str(e)}")
            return False