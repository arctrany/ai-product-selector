"""
场景级用户界面模块 - 处理场景相关的用户交互
包含Excel文件处理、数据管理和结果保存等场景特定功能
"""

import os
from datetime import datetime
from typing import Optional, Dict, Any, List


class SceneInterface:
    """场景级用户界面类 - 处理场景相关的用户交互"""

    def __init__(self, excel_file_path: Optional[str] = None):
        """
        初始化场景界面
        
        Args:
            excel_file_path: Excel文件路径，可以为空，后续通过set_excel_file设置
        """
        self.excel_file_path = excel_file_path
        self.stores_data = []
        self.crawled_results = []

    def set_excel_file(self, file_path: str) -> bool:
        """
        设置Excel文件路径
        
        Args:
            file_path: Excel文件路径
            
        Returns:
            bool: 设置是否成功
        """
        if not file_path:
            print("❌ 文件路径不能为空")
            return False

        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return False

        if not file_path.lower().endswith(('.xlsx', '.xls')):
            print("❌ 文件格式不支持，请使用Excel文件(.xlsx或.xls)")
            return False

        self.excel_file_path = file_path
        print(f"✅ Excel文件路径已设置: {file_path}")
        return True

    def get_default_excel_path(self) -> str:
        """
        获取默认的Excel文件路径
        
        Returns:
            str: 默认Excel文件路径
        """
        # 智能查找好店2.xlsx文件 - 优先使用用户的真实文件
        possible_paths = [
            "src/playweight/好店2.xlsx",  # 用户的真实文件（优先）
            "好店2.xlsx",  # 当前目录（项目根目录）
            "../好店2.xlsx",  # 上级目录
            "../../好店2.xlsx",  # 上上级目录
            "../../../好店2.xlsx",  # 更上级目录
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "好店2.xlsx"),  # 项目根目录绝对路径
            os.path.join(os.path.expanduser("~"), "好店2.xlsx"),  # 用户主目录
        ]

        for path in possible_paths:
            if os.path.exists(path):
                print(f"✅ 找到Excel文件: {path}")
                return path

        # 如果都找不到，创建一个示例文件
        print("⚠️ 未找到好店2.xlsx文件，创建示例数据...")
        return self.create_sample_excel()

    def read_stores_excel(self) -> bool:
        """
        读取店铺Excel文件
        
        Returns:
            bool: 读取是否成功
        """
        try:
            if not self.excel_file_path:
                # 直接使用默认路径，不再提示用户输入
                default_path = self.get_default_excel_path()
                if not self.set_excel_file(default_path):
                    return False

            print(f"📖 正在读取Excel文件: {self.excel_file_path}")

            if not os.path.exists(self.excel_file_path):
                print(f"❌ 文件不存在: {self.excel_file_path}")
                return False

            # 读取Excel文件
            try:
                import pandas as pd
                df = pd.read_excel(self.excel_file_path, engine='openpyxl')
                print(f"✅ 成功读取Excel文件，共 {len(df)} 行数据")

                # 转换为字典列表
                self.stores_data = df.to_dict('records')
            except ImportError:
                print("❌ 需要安装pandas: pip install pandas openpyxl")
                return False

            # 显示前几行数据作为预览
            print("📋 数据预览:")
            for i, store in enumerate(self.stores_data[:3], 1):
                print(f"  {i}. {store}")

            if len(self.stores_data) > 3:
                print(f"  ... 还有 {len(self.stores_data) - 3} 行数据")

            return True

        except Exception as e:
            print(f"❌ 读取Excel文件失败: {str(e)}")
            return False

    def get_stores_data(self) -> List[Dict[str, Any]]:
        """
        获取店铺数据
        
        Returns:
            List[Dict[str, Any]]: 店铺数据列表
        """
        return self.stores_data

    def set_crawled_results(self, results: List[Dict[str, Any]]):
        """
        设置爬取结果
        
        Args:
            results: 爬取结果列表
        """
        self.crawled_results = results

    def save_results_to_excel(self, output_path: Optional[str] = None) -> bool:
        """
        保存结果到Excel文件 - 包含商品数据
        
        Args:
            output_path: 输出文件路径，如果为None则自动生成
            
        Returns:
            bool: 保存是否成功
        """
        try:
            if not self.crawled_results:
                print("⚠️ 没有爬取结果需要保存")
                return False

            # 生成输出文件路径
            if not output_path:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_path = f"seerfar_stores_data_{timestamp}.xlsx"

            # 准备店铺数据
            store_data = []
            product_data = []

            for result in self.crawled_results:
                # 店铺数据
                store_row = {}
                if 'original_data' in result:
                    store_row.update(result['original_data'])

                store_row.update({
                    '爬取时间': result.get('extraction_time', ''),
                    '店铺ID': result.get('store_id', ''),
                    '店铺销售额_30天': result.get('sales_amount', ''),
                    '店铺销量_30天': result.get('sales_volume', ''),
                    '日均销量_30天': result.get('daily_avg_sales', ''),
                    '页面标题': result.get('page_title', ''),
                    '访问URL': result.get('url', ''),
                    '爬取成功': result.get('success', False),
                    '错误信息': result.get('error_message', ''),
                    '商品数量': len(result.get('products', []))
                })
                store_data.append(store_row)

                # 商品数据
                for product in result.get('products', []):
                    product_row = {
                        '店铺ID': result.get('store_id', ''),
                        '商品序号': product.get('product_index', ''),
                        '商品名称': product.get('product_name', ''),
                        '商品价格': product.get('product_price', ''),
                        '商品描述': product.get('product_description', ''),
                        '商品图片URL': product.get('product_image_url', ''),
                        '商品链接URL': product.get('product_link_url', ''),
                        '点击成功': product.get('click_success', False),
                        '提取时间': product.get('extraction_time', ''),
                        '错误信息': product.get('error_message', '')
                    }
                    product_data.append(product_row)

            # 保存到Excel文件（多个工作表）
            try:
                import pandas as pd
                with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                    # 店铺数据工作表
                    df_stores = pd.DataFrame(store_data)
                    df_stores.to_excel(writer, sheet_name='店铺数据', index=False)

                    # 商品数据工作表
                    if product_data:
                        df_products = pd.DataFrame(product_data)
                        df_products.to_excel(writer, sheet_name='商品数据', index=False)
                        print(f"✅ 保存商品数据: {len(df_products)} 行")
            except ImportError:
                print("❌ 需要安装pandas和openpyxl: pip install pandas openpyxl")
                return False

            print(f"✅ 爬取结果已保存到: {output_path}")
            print(f"📊 店铺数据: {len(store_data)} 行")
            print(f"🛍️ 商品数据: {len(product_data)} 行")

            return True

        except Exception as e:
            print(f"❌ 保存结果失败: {str(e)}")
            return False

    def display_statistics(self):
        """显示爬取统计信息"""
        if not self.crawled_results:
            print("⚠️ 没有爬取结果可显示")
            return

        successful_count = len([r for r in self.crawled_results if r.get('success')])
        failed_count = len([r for r in self.crawled_results if not r.get('success')])
        total_products = sum(len(r.get('products', [])) for r in self.crawled_results)

        print("\n" + "=" * 60)
        print("📊 爬取完成统计:")
        print(f"   总店铺数量: {len(self.crawled_results)}")
        print(f"   成功爬取: {successful_count}")
        print(f"   爬取失败: {failed_count}")
        print(f"   成功率: {(successful_count / len(self.crawled_results) * 100):.1f}%")
        print(f"   总商品数量: {total_products}")
        print("=" * 60)

    def prompt_for_limit(self) -> Optional[int]:
        """
        提示用户输入爬取数量限制
        
        Returns:
            Optional[int]: 爬取数量限制，None表示不限制
        """
        try:
            print(f"\n📊 当前共有 {len(self.stores_data)} 个店铺待爬取")
            limit_input = input("请输入要爬取的店铺数量 (按回车键爬取全部): ").strip()

            if not limit_input:
                return None

            limit = int(limit_input)
            if limit <= 0:
                print("❌ 数量必须大于0")
                return None

            if limit > len(self.stores_data):
                print(f"⚠️ 输入数量超过总数，将爬取全部 {len(self.stores_data)} 个店铺")
                return None

            return limit

        except ValueError:
            print("❌ 无效输入，请输入数字")
            return None
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return None

    def create_sample_excel(self) -> str:
        """
        创建示例Excel文件

        Returns:
            str: 创建的Excel文件路径
        """
        try:
            import pandas as pd

            # 创建示例数据
            sample_data = [
                {"store_id": "123456789", "name": "测试店铺1", "category": "电子产品"},
                {"store_id": "987654321", "name": "测试店铺2", "category": "服装"},
                {"store_id": "555666777", "name": "测试店铺3", "category": "家居用品"}
            ]

            df = pd.DataFrame(sample_data)
            excel_path = "好店2.xlsx"
            df.to_excel(excel_path, index=False, engine='openpyxl')

            print(f"✅ 已创建示例Excel文件: {excel_path}")
            print("📋 包含3个测试店铺数据")
            return excel_path

        except ImportError:
            print("❌ 需要安装pandas和openpyxl: pip install pandas openpyxl")
            return "好店2.xlsx"
        except Exception as e:
            print(f"❌ 创建示例文件失败: {str(e)}")
            return "好店2.xlsx"
