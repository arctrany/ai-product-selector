"""
用户交互层模块 - 负责接收用户输入和文件处理
提供用户友好的界面，处理Excel文件读取和结果保存
"""

import os
import pandas as pd
from datetime import datetime
from typing import Optional, Dict, Any, List


class UserInterface:
    """用户交互层类 - 处理用户输入和文件操作"""
    
    def __init__(self, excel_file_path: Optional[str] = None):
        """
        初始化用户交互层
        
        Args:
            excel_file_path: Excel文件路径，可以为空，后续通过set_excel_file设置
        """
        self.excel_file_path = excel_file_path
        self.stores_data = []
        self.crawled_results = []
        
        # 默认配置
        self.config = {
            'request_delay': 2,  # 请求间隔（秒）
            'page_timeout': 30000,  # 页面超时（毫秒）
            'max_retries': 3,  # 最大重试次数
            'output_format': 'xlsx',  # 输出格式
            'debug_mode': False  # 调试模式
        }
    
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
        # 智能查找好店2.xlsx文件
        possible_paths = [
            "好店2.xlsx",  # 当前目录
            "../../docs/好店2.xlsx",  # 项目docs目录
            "../../../docs/好店2.xlsx",  # 备用路径
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "docs", "好店2.xlsx")  # 绝对路径
        ]

        for path in possible_paths:
            if os.path.exists(path):
                return path

        # 如果都找不到，返回默认路径
        return "好店2.xlsx"
    
    def prompt_for_excel_file(self) -> bool:
        """
        提示用户选择Excel文件
        
        Returns:
            bool: 是否成功设置文件路径
        """
        print("📁 请选择Excel文件:")
        print("1. 使用默认文件路径")
        print("2. 输入自定义文件路径")
        
        try:
            choice = input("请选择 (1/2): ").strip()
            
            if choice == "1":
                default_path = self.get_default_excel_path()
                return self.set_excel_file(default_path)
            elif choice == "2":
                file_path = input("请输入Excel文件完整路径: ").strip()
                return self.set_excel_file(file_path)
            else:
                print("❌ 无效选择")
                return False
                
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return False
        except Exception as e:
            print(f"❌ 输入处理失败: {str(e)}")
            return False
    
    def read_stores_excel(self) -> bool:
        """
        读取店铺Excel文件
        
        Returns:
            bool: 读取是否成功
        """
        try:
            if not self.excel_file_path:
                print("⚠️ 未设置Excel文件路径")
                if not self.prompt_for_excel_file():
                    return False
            
            print(f"📖 正在读取Excel文件: {self.excel_file_path}")
            
            if not os.path.exists(self.excel_file_path):
                print(f"❌ 文件不存在: {self.excel_file_path}")
                return False
            
            # 读取Excel文件
            df = pd.read_excel(self.excel_file_path, engine='openpyxl')
            print(f"✅ 成功读取Excel文件，共 {len(df)} 行数据")
            
            # 转换为字典列表
            self.stores_data = df.to_dict('records')
            
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
    
    def get_config(self, key: str = None) -> Any:
        """
        获取配置项
        
        Args:
            key: 配置键名，如果为None则返回所有配置
            
        Returns:
            Any: 配置值或所有配置
        """
        if key is None:
            return self.config.copy()
        return self.config.get(key)
    
    def set_config(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        Args:
            key: 配置键名
            value: 配置值
            
        Returns:
            bool: 设置是否成功
        """
        if key in self.config:
            self.config[key] = value
            print(f"✅ 配置已更新: {key} = {value}")
            return True
        else:
            print(f"❌ 未知配置项: {key}")
            return False
    
    def prompt_for_config(self):
        """提示用户配置参数"""
        print("\n⚙️ 配置参数设置:")
        print("按回车键使用默认值")
        
        try:
            # 请求间隔
            delay_input = input(f"请求间隔(秒) [默认: {self.config['request_delay']}]: ").strip()
            if delay_input:
                try:
                    self.config['request_delay'] = float(delay_input)
                except ValueError:
                    print("⚠️ 无效输入，使用默认值")
            
            # 页面超时
            timeout_input = input(f"页面超时(秒) [默认: {self.config['page_timeout']//1000}]: ").strip()
            if timeout_input:
                try:
                    self.config['page_timeout'] = int(float(timeout_input) * 1000)
                except ValueError:
                    print("⚠️ 无效输入，使用默认值")
            
            # 调试模式
            debug_input = input(f"调试模式 (y/n) [默认: {'y' if self.config['debug_mode'] else 'n'}]: ").strip().lower()
            if debug_input in ['y', 'yes', 'true', '1']:
                self.config['debug_mode'] = True
            elif debug_input in ['n', 'no', 'false', '0']:
                self.config['debug_mode'] = False
            
            print("✅ 配置设置完成")
            
        except KeyboardInterrupt:
            print("\n⚠️ 配置设置被取消，使用默认配置")
    
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
                    # 店铺名称字段已删除 - 用户确认这是登录用户信息，不需要采集
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
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                # 店铺数据工作表
                df_stores = pd.DataFrame(store_data)
                df_stores.to_excel(writer, sheet_name='店铺数据', index=False)

                # 商品数据工作表
                if product_data:
                    df_products = pd.DataFrame(product_data)
                    df_products.to_excel(writer, sheet_name='商品数据', index=False)
                    print(f"✅ 保存商品数据: {len(df_products)} 行")

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
        print(f"   成功率: {(successful_count/len(self.crawled_results)*100):.1f}%")
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
    
    def show_welcome_message(self):
        """显示欢迎信息"""
        print("🚀 Seefar店铺数据爬取程序 - 模块化版本")
        print("📝 基于模块化设计，提供更好的可维护性和扩展性")
        print("=" * 60)
    
    def show_completion_message(self, success: bool, output_file: Optional[str] = None):
        """
        显示完成信息
        
        Args:
            success: 是否成功
            output_file: 输出文件路径
        """
        print(f"\n⏰ 结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        if success:
            print("\n✅ 程序运行成功！")
            print("📊 店铺数据已保存到Excel文件")
            if output_file:
                print(f"📁 输出文件: {output_file}")
        else:
            print("\n❌ 程序运行失败！")
            print("💡 请检查错误信息并重试")
    
    def confirm_operation(self, message: str) -> bool:
        """
        确认操作
        
        Args:
            message: 确认消息
            
        Returns:
            bool: 用户是否确认
        """
        try:
            response = input(f"{message} (y/n): ").strip().lower()
            return response in ['y', 'yes', 'true', '1']
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return False