"""
系统级用户交互模块 - 提供系统级的配置管理和通用UI功能
负责系统配置、通用用户交互，不涉及具体场景逻辑
"""

from datetime import datetime
from typing import Optional, Dict, Any

class UserInterface:
    """系统级用户交互类 - 处理系统配置和通用用户交互"""
    
    def __init__(self):
        """初始化系统级用户交互层"""
        # 默认系统配置
        self.config = {
            'request_delay': 2,  # 请求间隔（秒）
            'page_timeout': 30000,  # 页面超时（毫秒）
            'max_retries': 3,  # 最大重试次数
            'output_format': 'xlsx',  # 输出格式
            'debug_mode': False  # 调试模式
        }
    
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
        print("\n⚙️ 系统配置参数设置:")
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
            
            print("✅ 系统配置设置完成")
            
        except KeyboardInterrupt:
            print("\n⚠️ 配置设置被取消，使用默认配置")
    
    def show_welcome_message(self):
        """显示系统欢迎信息"""
        print("🚀 浏览器自动化系统 - 模块化架构")
        print("📝 基于Runner模式设计，支持多种场景扩展")
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
            print("\n✅ 系统运行成功！")
            if output_file:
                print(f"📁 输出文件: {output_file}")
        else:
            print("\n❌ 系统运行失败！")
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
    
    def show_system_info(self):
        """显示系统信息"""
        print("\n📋 系统配置信息:")
        for key, value in self.config.items():
            print(f"   {key}: {value}")
    
    def prompt_for_choice(self, message: str, choices: list) -> Optional[str]:
        """
        提示用户选择
        
        Args:
            message: 提示消息
            choices: 选择列表
            
        Returns:
            Optional[str]: 用户选择，None表示取消
        """
        try:
            print(f"\n{message}")
            for i, choice in enumerate(choices, 1):
                print(f"{i}. {choice}")
            
            choice_input = input("请选择: ").strip()
            
            if choice_input.isdigit():
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(choices):
                    return choices[choice_index]
            
            print("❌ 无效选择")
            return None
            
        except KeyboardInterrupt:
            print("\n❌ 用户取消操作")
            return None
    
    def show_progress(self, current: int, total: int, message: str = ""):
        """
        显示进度信息
        
        Args:
            current: 当前进度
            total: 总数
            message: 附加消息
        """
        percentage = (current / total * 100) if total > 0 else 0
        progress_bar = "█" * int(percentage // 5) + "░" * (20 - int(percentage // 5))
        print(f"\r📊 进度: [{progress_bar}] {percentage:.1f}% ({current}/{total}) {message}", end="", flush=True)
        
        if current >= total:
            print()  # 完成时换行

    def display_statistics(self):
        """显示系统统计信息"""
        print("\n📊 系统运行统计:")
        print(f"   ⚙️ 当前配置: {len(self.config)} 项")
        print(f"   🕒 运行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   🔧 调试模式: {'开启' if self.config.get('debug_mode', False) else '关闭'}")
        print(f"   ⏱️ 请求间隔: {self.config.get('request_delay', 2)} 秒")
        print(f"   📄 输出格式: {self.config.get('output_format', 'xlsx')}")
        print("   ✅ 系统状态: 正常运行")