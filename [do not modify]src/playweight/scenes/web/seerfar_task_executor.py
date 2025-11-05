"""
Seerfar场景任务执行器 - 业务层
专门处理智能选品相关的任务执行逻辑
"""

import asyncio
from typing import Dict, Any, Optional, List
from playweight.runner import Runner


class SeerfarTaskExecutor:
    """Seerfar场景任务执行器"""
    
    def __init__(self):
        """初始化执行器"""
        self.runner = None
        self.current_scenario = None
    
    def get_task_config(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据表单数据获取任务配置
        
        Args:
            form_data: 表单数据
            
        Returns:
            Dict[str, Any]: 任务配置
        """
        # 根据表单数据动态确定任务配置
        total_items = form_data.get('max_products_per_store', 10)
        
        return {
            'name': '智能选品自动化任务',
            'total_items': total_items
        }
    
    async def execute_task(self, task_id: str, form_data: Dict[str, Any], context: Dict[str, Any]):
        """
        执行智能选品任务
        
        Args:
            task_id: 任务ID
            form_data: 表单数据
            context: 执行上下文，包含web_console、task_stop_flag等
        """
        web_console = context.get('web_console')
        task_stop_flag = context.get('task_stop_flag')
        set_current_runner = context.get('set_current_runner')
        
        try:
            web_console.info(f"🚀 开始执行智能选品任务: {task_id}")
            web_console.info(f"📋 表单数据: {list(form_data.keys())}")
            
            # 创建Runner实例
            self.runner = Runner()
            
            # 设置当前runner到全局上下文，用于截图等功能
            if set_current_runner:
                set_current_runner(self.runner)
            
            # 加载智能选品场景
            scenario = await self._load_seerfar_scenario(form_data, web_console)
            if not scenario:
                raise Exception("智能选品场景加载失败")
            
            # 设置场景到runner
            self.runner.set_scenario(scenario)
            self.current_scenario = scenario
            
            # 直接执行AutomationScenario的工作流程
            web_console.info("🔧 开始初始化系统...")

            # 初始化浏览器和页面
            if not await self.runner.initialize_system():
                raise Exception("系统初始化失败")

            # 设置用户界面
            if not self.runner.setup_user_interface():
                raise Exception("用户界面设置失败")

            # 准备店铺数据
            stores_data = await self._prepare_stores_data(form_data, web_console)
            if not stores_data:
                raise Exception("店铺数据准备失败")

            # 执行批量店铺爬取
            web_console.info(f"🚀 开始执行智能选品，共 {len(stores_data)} 个店铺")
            results = await scenario.crawl_all_stores(stores_data)

            if results:
                web_console.success(f"✅ 智能选品任务执行成功完成，处理了 {len(results)} 个店铺")
            else:
                web_console.error("❌ 智能选品任务执行失败")
                raise Exception("智能选品任务执行失败")
                
        except Exception as e:
            web_console.error(f"❌ 智能选品任务执行异常: {str(e)}")
            raise
    
    async def _load_seerfar_scenario(self, form_data: Dict[str, Any], web_console) -> Optional[Any]:
        """
        加载智能选品场景
        
        Args:
            form_data: 表单数据
            web_console: 控制台对象
            
        Returns:
            场景实例或None
        """
        try:
            # 加载智能选品场景
            from playweight.scenes.automation_scenario import AutomationScenario

            web_console.info("📦 正在加载智能选品场景...")
            scenario = AutomationScenario()
            
            # 传递表单数据给场景
            if hasattr(scenario, 'set_form_data'):
                scenario.set_form_data(form_data)
            
            web_console.success("✅ 智能选品场景加载成功")
            return scenario
            
        except ImportError as e:
            web_console.error(f"❌ 智能选品场景模块导入失败: {str(e)}")
            web_console.warning("💡 请确保SeerfarScenario类存在且可导入")
            return None
        except Exception as e:
            web_console.error(f"❌ 智能选品场景加载异常: {str(e)}")
            return None
    
    def get_runner(self) -> Optional[Runner]:
        """获取当前的Runner实例"""
        return self.runner
    
    def get_scenario(self) -> Optional[Any]:
        """获取当前的场景实例"""
        return self.current_scenario

    async def _prepare_stores_data(self, form_data: Dict[str, Any], web_console) -> Optional[List[Dict[str, Any]]]:
        """
        准备店铺数据

        Args:
            form_data: 表单数据
            web_console: 控制台对象

        Returns:
            店铺数据列表或None
        """
        try:
            # 获取好店文件路径
            good_shop_file = form_data.get('good_shop_file')
            if not good_shop_file:
                web_console.error("❌ 未找到好店模版文件")
                return None

            web_console.info(f"📂 正在读取好店文件: {good_shop_file}")

            # 读取Excel文件
            import pandas as pd
            df = pd.read_excel(good_shop_file)

            # 转换为店铺数据格式
            stores_data = []
            for index, row in df.iterrows():
                # 假设Excel第一列是店铺ID
                store_info = {}
                for col_index, value in enumerate(row):
                    if pd.notna(value):
                        if col_index == 0:  # 第一列作为店铺ID
                            store_info['store_id'] = str(value).strip()
                        else:
                            store_info[f'column_{col_index}'] = str(value).strip()

                if store_info.get('store_id'):
                    stores_data.append(store_info)

            web_console.success(f"✅ 成功读取 {len(stores_data)} 个店铺数据")
            return stores_data

        except Exception as e:
            web_console.error(f"❌ 店铺数据准备失败: {str(e)}")
            return None