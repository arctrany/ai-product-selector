#!/usr/bin/env python3
"""
智能选品系统交互式命令行界面

提供完整的命令行交互功能，包括配置管理、任务控制、进度监控等
"""

import sys
import os
import threading
import time
import signal
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from apps.xuanping.ui.models import UIConfig, AppState, LogLevel, ui_state_manager
    from apps.xuanping.ui.task_controller import task_controller
    from apps.xuanping.ui.preset_manager import preset_manager
    from apps.xuanping.ui.log_manager import log_manager, LogExportFormat
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有依赖模块都已正确安装")
    sys.exit(1)

class CLIColors:
    """命令行颜色常量"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class ProgressDisplay:
    """进度显示器"""
    
    def __init__(self):
        self.last_update = 0
        self.running = False
        self.thread = None
    
    def start(self):
        """开始显示进度"""
        self.running = True
        self.thread = threading.Thread(target=self._update_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止显示进度"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
    
    def _update_loop(self):
        """进度更新循环"""
        while self.running:
            try:
                status = task_controller.get_task_status()
                if status and 'processing_stats' in status:
                    self._display_progress(status['processing_stats'])
                time.sleep(2)
            except Exception as e:
                print(f"\r{CLIColors.FAIL}进度更新错误: {e}{CLIColors.ENDC}")
                break
    
    def _display_progress(self, stats):
        """显示进度信息"""
        if not stats:
            return
        
        total = stats.get('total_stores', 0)
        processed = stats.get('processed_stores', 0)
        good = stats.get('good_stores', 0)
        current = stats.get('current_store', '')
        step = stats.get('current_step', '')
        
        if total > 0:
            percentage = (processed / total) * 100
            bar_length = 30
            filled_length = int(bar_length * processed // total)
            bar = '█' * filled_length + '░' * (bar_length - filled_length)
            
            progress_text = (
                f"\r{CLIColors.OKBLUE}进度: [{bar}] {percentage:.1f}% "
                f"({processed}/{total}) | 好店: {good} | {step}"
                f"{CLIColors.ENDC}"
            )
            
            if current:
                progress_text += f" | 当前: {current[:20]}..."
            
            print(progress_text, end='', flush=True)

class XuanpingCLI:
    """智能选品系统命令行界面"""
    
    def __init__(self):
        self.current_config = UIConfig()
        self.progress_display = ProgressDisplay()
        self.running = True
        self._setup_signal_handlers()
        self._subscribe_events()
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, frame):
            print(f"\n{CLIColors.WARNING}接收到中断信号，正在退出...{CLIColors.ENDC}")
            self.running = False
            self.progress_display.stop()
            if ui_state_manager.state in [AppState.RUNNING, AppState.PAUSED]:
                task_controller.stop_task()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def _subscribe_events(self):
        """订阅事件"""
        ui_state_manager.subscribe(ui_state_manager.EventType.STATE_CHANGED, self._on_state_changed)
        ui_state_manager.subscribe(ui_state_manager.EventType.LOG_ADDED, self._on_log_added)
    
    def _on_state_changed(self, event):
        """状态变化处理"""
        state = event.data
        state_text = {
            AppState.IDLE: "等待开始",
            AppState.RUNNING: "运行中",
            AppState.PAUSED: "已暂停",
            AppState.STOPPING: "正在停止",
            AppState.COMPLETED: "已完成",
            AppState.ERROR: "出错"
        }
        
        color = {
            AppState.IDLE: CLIColors.OKBLUE,
            AppState.RUNNING: CLIColors.OKGREEN,
            AppState.PAUSED: CLIColors.WARNING,
            AppState.STOPPING: CLIColors.WARNING,
            AppState.COMPLETED: CLIColors.OKGREEN,
            AppState.ERROR: CLIColors.FAIL
        }
        
        status_color = color.get(state, CLIColors.ENDC)
        status_msg = state_text.get(state, "未知状态")
        
        print(f"\n{status_color}[状态] {status_msg}{CLIColors.ENDC}")
        
        if state == AppState.RUNNING:
            self.progress_display.start()
        elif state in [AppState.COMPLETED, AppState.ERROR, AppState.IDLE]:
            self.progress_display.stop()
            print()  # 换行
    
    def _on_log_added(self, event):
        """日志添加处理"""
        log_entry = event.data
        
        color_map = {
            LogLevel.INFO: CLIColors.OKBLUE,
            LogLevel.SUCCESS: CLIColors.OKGREEN,
            LogLevel.WARNING: CLIColors.WARNING,
            LogLevel.ERROR: CLIColors.FAIL
        }
        
        color = color_map.get(log_entry.level, CLIColors.ENDC)
        timestamp = log_entry.timestamp.strftime('%H:%M:%S')
        level = log_entry.level.value.upper()
        
        # 如果正在显示进度，先换行
        if self.progress_display.running:
            print()
        
        print(f"{color}[{timestamp}] [{level}] {log_entry.message}{CLIColors.ENDC}")
    
    def print_header(self):
        """打印标题"""
        header = f"""
{CLIColors.HEADER}{CLIColors.BOLD}
╔══════════════════════════════════════════════════════════════╗
║                    🎯 智能选品系统 CLI                        ║
║                  AI-Powered Product Selector                ║
╚══════════════════════════════════════════════════════════════╝
{CLIColors.ENDC}
{CLIColors.OKBLUE}基于AI驱动的OZON好店筛选与利润分析平台{CLIColors.ENDC}
"""
        print(header)
    
    def print_menu(self):
        """打印主菜单"""
        state = ui_state_manager.state
        
        menu = f"""
{CLIColors.BOLD}主菜单:{CLIColors.ENDC}
{CLIColors.OKBLUE}1.{CLIColors.ENDC} 配置参数
{CLIColors.OKBLUE}2.{CLIColors.ENDC} 预设管理
{CLIColors.OKBLUE}3.{CLIColors.ENDC} 任务控制
{CLIColors.OKBLUE}4.{CLIColors.ENDC} 查看日志
{CLIColors.OKBLUE}5.{CLIColors.ENDC} 导出日志
{CLIColors.OKBLUE}6.{CLIColors.ENDC} 系统状态
{CLIColors.OKBLUE}0.{CLIColors.ENDC} 退出系统

{CLIColors.BOLD}当前状态:{CLIColors.ENDC} """
        
        state_color = {
            AppState.IDLE: CLIColors.OKBLUE,
            AppState.RUNNING: CLIColors.OKGREEN,
            AppState.PAUSED: CLIColors.WARNING,
            AppState.STOPPING: CLIColors.WARNING,
            AppState.COMPLETED: CLIColors.OKGREEN,
            AppState.ERROR: CLIColors.FAIL
        }.get(state, CLIColors.ENDC)
        
        state_text = {
            AppState.IDLE: "等待开始",
            AppState.RUNNING: "运行中",
            AppState.PAUSED: "已暂停",
            AppState.STOPPING: "正在停止",
            AppState.COMPLETED: "已完成",
            AppState.ERROR: "出错"
        }.get(state, "未知")
        
        print(menu + f"{state_color}{state_text}{CLIColors.ENDC}")
    
    def configure_parameters(self):
        """配置参数"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 配置参数 ==={CLIColors.ENDC}")
        
        while True:
            print(f"""
{CLIColors.BOLD}当前配置:{CLIColors.ENDC}
1. 好店模版文件: {CLIColors.OKCYAN}{self.current_config.good_shop_file or '未设置'}{CLIColors.ENDC}
2. 采品文件: {CLIColors.OKCYAN}{self.current_config.item_collect_file or '未设置'}{CLIColors.ENDC}
3. 计算器文件: {CLIColors.OKCYAN}{self.current_config.margin_calculator or '未设置'}{CLIColors.ENDC}
4. 输出路径: {CLIColors.OKCYAN}{self.current_config.output_path or '未设置'}{CLIColors.ENDC}
5. 利润率阈值: {CLIColors.OKCYAN}{self.current_config.margin:.2%}{CLIColors.ENDC}
6. 每店铺最大商品数: {CLIColors.OKCYAN}{self.current_config.max_products_per_store}{CLIColors.ENDC}

{CLIColors.BOLD}选择要修改的配置项 (1-6) 或输入 0 返回:{CLIColors.ENDC} """, end="")
            
            choice = input().strip()
            
            if choice == '0':
                break
            elif choice == '1':
                self._input_file_path("好店模版文件", "good_shop_file")
            elif choice == '2':
                self._input_file_path("采品文件", "item_collect_file")
            elif choice == '3':
                self._input_file_path("计算器文件", "margin_calculator")
            elif choice == '4':
                self._input_directory_path("输出路径", "output_path")
            elif choice == '5':
                self._input_margin()
            elif choice == '6':
                self._input_max_products()
            else:
                print(f"{CLIColors.FAIL}无效选择，请重新输入{CLIColors.ENDC}")
    
    def _input_file_path(self, name: str, attr: str):
        """输入文件路径"""
        print(f"\n{CLIColors.BOLD}设置{name}:{CLIColors.ENDC}")
        print("请输入文件路径 (留空取消):")
        
        path = input().strip()
        if path:
            if os.path.exists(path):
                setattr(self.current_config, attr, path)
                print(f"{CLIColors.OKGREEN}✓ {name}已设置为: {path}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 文件不存在: {path}{CLIColors.ENDC}")
    
    def _input_directory_path(self, name: str, attr: str):
        """输入目录路径"""
        print(f"\n{CLIColors.BOLD}设置{name}:{CLIColors.ENDC}")
        print("请输入目录路径 (留空取消):")
        
        path = input().strip()
        if path:
            if os.path.exists(path) and os.path.isdir(path):
                setattr(self.current_config, attr, path)
                print(f"{CLIColors.OKGREEN}✓ {name}已设置为: {path}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 目录不存在: {path}{CLIColors.ENDC}")
    
    def _input_margin(self):
        """输入利润率"""
        print(f"\n{CLIColors.BOLD}设置利润率阈值:{CLIColors.ENDC}")
        print(f"当前值: {self.current_config.margin:.2%}")
        print("请输入新的利润率 (0.0-1.0，如 0.15 表示 15%):")
        
        try:
            value = float(input().strip())
            if 0.0 <= value <= 1.0:
                self.current_config.margin = value
                print(f"{CLIColors.OKGREEN}✓ 利润率阈值已设置为: {value:.2%}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 利润率必须在 0.0-1.0 之间{CLIColors.ENDC}")
        except ValueError:
            print(f"{CLIColors.FAIL}✗ 请输入有效的数字{CLIColors.ENDC}")
    
    def _input_max_products(self):
        """输入最大商品数"""
        print(f"\n{CLIColors.BOLD}设置每店铺最大商品数:{CLIColors.ENDC}")
        print(f"当前值: {self.current_config.max_products_per_store}")
        print("请输入新的最大商品数 (1-1000):")
        
        try:
            value = int(input().strip())
            if 1 <= value <= 1000:
                self.current_config.max_products_per_store = value
                print(f"{CLIColors.OKGREEN}✓ 最大商品数已设置为: {value}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 最大商品数必须在 1-1000 之间{CLIColors.ENDC}")
        except ValueError:
            print(f"{CLIColors.FAIL}✗ 请输入有效的整数{CLIColors.ENDC}")
    
    def manage_presets(self):
        """预设管理"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 预设管理 ==={CLIColors.ENDC}")
        
        while True:
            try:
                presets = preset_manager.list_presets()
                
                print(f"""
{CLIColors.BOLD}可用预设:{CLIColors.ENDC}""")
                
                if presets:
                    for i, preset in enumerate(presets, 1):
                        print(f"{CLIColors.OKBLUE}{i}.{CLIColors.ENDC} {preset}")
                else:
                    print(f"{CLIColors.WARNING}暂无预设{CLIColors.ENDC}")
                
                print(f"""
{CLIColors.BOLD}操作选项:{CLIColors.ENDC}
{CLIColors.OKBLUE}1.{CLIColors.ENDC} 加载预设
{CLIColors.OKBLUE}2.{CLIColors.ENDC} 保存当前配置为预设
{CLIColors.OKBLUE}3.{CLIColors.ENDC} 删除预设
{CLIColors.OKBLUE}0.{CLIColors.ENDC} 返回主菜单

请选择操作: """, end="")
                
                choice = input().strip()
                
                if choice == '0':
                    break
                elif choice == '1':
                    self._load_preset(presets)
                elif choice == '2':
                    self._save_preset()
                elif choice == '3':
                    self._delete_preset(presets)
                else:
                    print(f"{CLIColors.FAIL}无效选择，请重新输入{CLIColors.ENDC}")
                    
            except Exception as e:
                print(f"{CLIColors.FAIL}预设管理错误: {e}{CLIColors.ENDC}")
                break
    
    def _load_preset(self, presets):
        """加载预设"""
        if not presets:
            print(f"{CLIColors.WARNING}没有可用的预设{CLIColors.ENDC}")
            return
        
        print("请输入要加载的预设编号或名称:")
        choice = input().strip()
        
        preset_name = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                preset_name = presets[idx]
        else:
            if choice in presets:
                preset_name = choice
        
        if preset_name:
            try:
                config = preset_manager.load_preset(preset_name)
                self.current_config = config
                print(f"{CLIColors.OKGREEN}✓ 预设 '{preset_name}' 已加载{CLIColors.ENDC}")
            except Exception as e:
                print(f"{CLIColors.FAIL}✗ 加载预设失败: {e}{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 无效的预设选择{CLIColors.ENDC}")
    
    def _save_preset(self):
        """保存预设"""
        print("请输入预设名称:")
        name = input().strip()
        
        if name:
            try:
                preset_manager.save_preset(name, self.current_config)
                print(f"{CLIColors.OKGREEN}✓ 预设 '{name}' 已保存{CLIColors.ENDC}")
            except Exception as e:
                print(f"{CLIColors.FAIL}✗ 保存预设失败: {e}{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 预设名称不能为空{CLIColors.ENDC}")
    
    def _delete_preset(self, presets):
        """删除预设"""
        if not presets:
            print(f"{CLIColors.WARNING}没有可用的预设{CLIColors.ENDC}")
            return
        
        print("请输入要删除的预设编号或名称:")
        choice = input().strip()
        
        preset_name = None
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(presets):
                preset_name = presets[idx]
        else:
            if choice in presets:
                preset_name = choice
        
        if preset_name:
            print(f"确定要删除预设 '{preset_name}' 吗? (y/N): ", end="")
            confirm = input().strip().lower()
            
            if confirm == 'y':
                try:
                    preset_manager.delete_preset(preset_name)
                    print(f"{CLIColors.OKGREEN}✓ 预设 '{preset_name}' 已删除{CLIColors.ENDC}")
                except Exception as e:
                    print(f"{CLIColors.FAIL}✗ 删除预设失败: {e}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.WARNING}取消删除{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 无效的预设选择{CLIColors.ENDC}")
    
    def task_control(self):
        """任务控制"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 任务控制 ==={CLIColors.ENDC}")
        
        state = ui_state_manager.state
        
        print(f"\n{CLIColors.BOLD}当前状态:{CLIColors.ENDC} ", end="")
        
        state_color = {
            AppState.IDLE: CLIColors.OKBLUE,
            AppState.RUNNING: CLIColors.OKGREEN,
            AppState.PAUSED: CLIColors.WARNING,
            AppState.STOPPING: CLIColors.WARNING,
            AppState.COMPLETED: CLIColors.OKGREEN,
            AppState.ERROR: CLIColors.FAIL
        }.get(state, CLIColors.ENDC)
        
        state_text = {
            AppState.IDLE: "等待开始",
            AppState.RUNNING: "运行中",
            AppState.PAUSED: "已暂停",
            AppState.STOPPING: "正在停止",
            AppState.COMPLETED: "已完成",
            AppState.ERROR: "出错"
        }.get(state, "未知")
        
        print(f"{state_color}{state_text}{CLIColors.ENDC}")
        
        # 根据状态显示可用操作
        available_actions = []
        
        if state == AppState.IDLE:
            available_actions.append(("1", "开始任务", self._start_task))
        elif state == AppState.RUNNING:
            available_actions.append(("1", "暂停任务", self._pause_task))
            available_actions.append(("2", "停止任务", self._stop_task))
        elif state == AppState.PAUSED:
            available_actions.append(("1", "继续任务", self._resume_task))
            available_actions.append(("2", "停止任务", self._stop_task))
        elif state in [AppState.COMPLETED, AppState.ERROR]:
            available_actions.append(("1", "重新开始", self._start_task))
        
        if available_actions:
            print(f"\n{CLIColors.BOLD}可用操作:{CLIColors.ENDC}")
            for code, desc, _ in available_actions:
                print(f"{CLIColors.OKBLUE}{code}.{CLIColors.ENDC} {desc}")
            
            print(f"{CLIColors.OKBLUE}0.{CLIColors.ENDC} 返回主菜单")
            print("\n请选择操作: ", end="")
            
            choice = input().strip()
            
            if choice == '0':
                return
            
            for code, _, action in available_actions:
                if choice == code:
                    action()
                    return
            
            print(f"{CLIColors.FAIL}无效选择{CLIColors.ENDC}")
        else:
            print(f"\n{CLIColors.WARNING}当前状态下没有可用操作{CLIColors.ENDC}")
            input("按回车键返回...")
    
    def _start_task(self):
        """开始任务"""
        # 验证配置
        if not self.current_config.good_shop_file:
            print(f"{CLIColors.FAIL}✗ 请先设置好店模版文件{CLIColors.ENDC}")
            return
        
        if not self.current_config.output_path:
            print(f"{CLIColors.FAIL}✗ 请先设置输出路径{CLIColors.ENDC}")
            return
        
        if not os.path.exists(self.current_config.good_shop_file):
            print(f"{CLIColors.FAIL}✗ 好店模版文件不存在{CLIColors.ENDC}")
            return
        
        if not os.path.exists(self.current_config.output_path):
            print(f"{CLIColors.FAIL}✗ 输出路径不存在{CLIColors.ENDC}")
            return
        
        print(f"{CLIColors.OKGREEN}正在启动任务...{CLIColors.ENDC}")
        success = task_controller.start_task(self.current_config)
        
        if success:
            print(f"{CLIColors.OKGREEN}✓ 任务已启动{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 任务启动失败{CLIColors.ENDC}")
    
    def _pause_task(self):
        """暂停任务"""
        print(f"{CLIColors.WARNING}正在暂停任务...{CLIColors.ENDC}")
        success = task_controller.pause_task()
        
        if success:
            print(f"{CLIColors.OKGREEN}✓ 任务已暂停{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 任务暂停失败{CLIColors.ENDC}")
    
    def _resume_task(self):
        """继续任务"""
        print(f"{CLIColors.OKGREEN}正在继续任务...{CLIColors.ENDC}")
        success = task_controller.resume_task()
        
        if success:
            print(f"{CLIColors.OKGREEN}✓ 任务已继续{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.FAIL}✗ 任务继续失败{CLIColors.ENDC}")
    
    def _stop_task(self):
        """停止任务"""
        print("确定要停止当前任务吗? (y/N): ", end="")
        confirm = input().strip().lower()
        
        if confirm == 'y':
            print(f"{CLIColors.WARNING}正在停止任务...{CLIColors.ENDC}")
            success = task_controller.stop_task()
            
            if success:
                print(f"{CLIColors.OKGREEN}✓ 任务已停止{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 任务停止失败{CLIColors.ENDC}")
        else:
            print(f"{CLIColors.WARNING}取消停止{CLIColors.ENDC}")
    
    def view_logs(self):
        """查看日志"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 查看日志 ==={CLIColors.ENDC}")
        
        logs = ui_state_manager.logs
        
        if not logs:
            print(f"{CLIColors.WARNING}暂无日志{CLIColors.ENDC}")
            input("按回车键返回...")
            return
        
        print(f"\n{CLIColors.BOLD}最近 20 条日志:{CLIColors.ENDC}")
        
        recent_logs = logs[-20:] if len(logs) > 20 else logs
        
        for log_entry in recent_logs:
            color_map = {
                LogLevel.INFO: CLIColors.OKBLUE,
                LogLevel.SUCCESS: CLIColors.OKGREEN,
                LogLevel.WARNING: CLIColors.WARNING,
                LogLevel.ERROR: CLIColors.FAIL
            }
            
            color = color_map.get(log_entry.level, CLIColors.ENDC)
            timestamp = log_entry.timestamp.strftime('%H:%M:%S')
            level = log_entry.level.value.upper()
            
            print(f"{color}[{timestamp}] [{level}] {log_entry.message}{CLIColors.ENDC}")
        
        if len(logs) > 20:
            print(f"\n{CLIColors.WARNING}显示了最近 20 条日志，共有 {len(logs)} 条日志{CLIColors.ENDC}")
        
        input("\n按回车键返回...")
    
    def export_logs(self):
        """导出日志"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 导出日志 ==={CLIColors.ENDC}")
        
        logs = ui_state_manager.logs
        
        if not logs:
            print(f"{CLIColors.WARNING}暂无日志可导出{CLIColors.ENDC}")
            input("按回车键返回...")
            return
        
        print(f"""
{CLIColors.BOLD}导出格式:{CLIColors.ENDC}
{CLIColors.OKBLUE}1.{CLIColors.ENDC} TXT 格式
{CLIColors.OKBLUE}2.{CLIColors.ENDC} CSV 格式
{CLIColors.OKBLUE}3.{CLIColors.ENDC} JSON 格式
{CLIColors.OKBLUE}4.{CLIColors.ENDC} HTML 格式
{CLIColors.OKBLUE}0.{CLIColors.ENDC} 返回

请选择格式: """, end="")
        
        choice = input().strip()
        
        format_map = {
            '1': LogExportFormat.TXT,
            '2': LogExportFormat.CSV,
            '3': LogExportFormat.JSON,
            '4': LogExportFormat.HTML
        }
        
        if choice == '0':
            return
        
        if choice not in format_map:
            print(f"{CLIColors.FAIL}无效选择{CLIColors.ENDC}")
            return
        
        export_format = format_map[choice]
        
        # 生成默认文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        ext = choice_to_ext = {'1': 'txt', '2': 'csv', '3': 'json', '4': 'html'}[choice]
        default_filename = f"xuanping_logs_{timestamp}.{ext}"
        
        print(f"请输入导出文件路径 (默认: {default_filename}):")
        filename = input().strip()
        
        if not filename:
            filename = default_filename
        
        try:
            success = log_manager.export_logs(logs, filename, export_format)
            
            if success:
                print(f"{CLIColors.OKGREEN}✓ 日志已导出到: {filename}{CLIColors.ENDC}")
            else:
                print(f"{CLIColors.FAIL}✗ 导出日志失败{CLIColors.ENDC}")
                
        except Exception as e:
            print(f"{CLIColors.FAIL}✗ 导出日志失败: {e}{CLIColors.ENDC}")
        
        input("按回车键返回...")
    
    def show_system_status(self):
        """显示系统状态"""
        print(f"\n{CLIColors.HEADER}{CLIColors.BOLD}=== 系统状态 ==={CLIColors.ENDC}")
        
        # 获取任务状态
        try:
            status = task_controller.get_task_status()
            
            print(f"\n{CLIColors.BOLD}任务状态:{CLIColors.ENDC}")
            
            state = ui_state_manager.state
            state_color = {
                AppState.IDLE: CLIColors.OKBLUE,
                AppState.RUNNING: CLIColors.OKGREEN,
                AppState.PAUSED: CLIColors.WARNING,
                AppState.STOPPING: CLIColors.WARNING,
                AppState.COMPLETED: CLIColors.OKGREEN,
                AppState.ERROR: CLIColors.FAIL
            }.get(state, CLIColors.ENDC)
            
            state_text = {
                AppState.IDLE: "等待开始",
                AppState.RUNNING: "运行中",
                AppState.PAUSED: "已暂停",
                AppState.STOPPING: "正在停止",
                AppState.COMPLETED: "已完成",
                AppState.ERROR: "出错"
            }.get(state, "未知")
            
            print(f"状态: {state_color}{state_text}{CLIColors.ENDC}")
            
            if status and 'processing_stats' in status:
                stats = status['processing_stats']
                print(f"总店铺数: {CLIColors.OKCYAN}{stats.get('total_stores', 0)}{CLIColors.ENDC}")
                print(f"已处理: {CLIColors.OKCYAN}{stats.get('processed_stores', 0)}{CLIColors.ENDC}")
                print(f"好店数: {CLIColors.OKGREEN}{stats.get('good_stores', 0)}{CLIColors.ENDC}")
                print(f"当前步骤: {CLIColors.OKCYAN}{stats.get('current_step', '无')}{CLIColors.ENDC}")
                
                if stats.get('current_store'):
                    print(f"当前店铺: {CLIColors.OKCYAN}{stats['current_store']}{CLIColors.ENDC}")
            
            # 显示配置信息
            print(f"\n{CLIColors.BOLD}当前配置:{CLIColors.ENDC}")
            print(f"好店模版文件: {CLIColors.OKCYAN}{self.current_config.good_shop_file or '未设置'}{CLIColors.ENDC}")
            print(f"输出路径: {CLIColors.OKCYAN}{self.current_config.output_path or '未设置'}{CLIColors.ENDC}")
            print(f"利润率阈值: {CLIColors.OKCYAN}{self.current_config.margin:.2%}{CLIColors.ENDC}")
            print(f"最大商品数: {CLIColors.OKCYAN}{self.current_config.max_products_per_store}{CLIColors.ENDC}")
            
            # 显示日志统计
            logs = ui_state_manager.logs
            if logs:
                log_counts = {}
                for log in logs:
                    level = log.level.value
                    log_counts[level] = log_counts.get(level, 0) + 1
                
                print(f"\n{CLIColors.BOLD}日志统计:{CLIColors.ENDC}")
                for level, count in log_counts.items():
                    color = {
                        'info': CLIColors.OKBLUE,
                        'success': CLIColors.OKGREEN,
                        'warning': CLIColors.WARNING,
                        'error': CLIColors.FAIL
                    }.get(level, CLIColors.ENDC)
                    
                    print(f"{level.upper()}: {color}{count}{CLIColors.ENDC}")
            
        except Exception as e:
            print(f"{CLIColors.FAIL}获取系统状态失败: {e}{CLIColors.ENDC}")
        
        input("\n按回车键返回...")
    
    def run(self):
        """运行CLI应用"""
        try:
            self.print_header()
            
            # 添加启动日志
            ui_state_manager.add_log(LogLevel.INFO, "智能选品系统CLI已启动")
            ui_state_manager.add_log(LogLevel.INFO, "请配置参数后开始任务")
            
            while self.running:
                try:
                    self.print_menu()
                    print(f"\n{CLIColors.BOLD}请选择操作 (0-6):{CLIColors.ENDC} ", end="")
                    
                    choice = input().strip()
                    
                    if choice == '0':
                        print(f"{CLIColors.OKBLUE}感谢使用智能选品系统！{CLIColors.ENDC}")
                        break
                    elif choice == '1':
                        self.configure_parameters()
                    elif choice == '2':
                        self.manage_presets()
                    elif choice == '3':
                        self.task_control()
                    elif choice == '4':
                        self.view_logs()
                    elif choice == '5':
                        self.export_logs()
                    elif choice == '6':
                        self.show_system_status()
                    else:
                        print(f"{CLIColors.FAIL}无效选择，请输入 0-6{CLIColors.ENDC}")
                
                except KeyboardInterrupt:
                    print(f"\n{CLIColors.WARNING}检测到中断信号{CLIColors.ENDC}")
                    break
                except EOFError:
                    print(f"\n{CLIColors.WARNING}输入结束{CLIColors.ENDC}")
                    break
                except Exception as e:
                    print(f"{CLIColors.FAIL}操作错误: {e}{CLIColors.ENDC}")
                    input("按回车键继续...")
        
        finally:
            self.progress_display.stop()
            
            # 如果有正在运行的任务，询问是否停止
            if ui_state_manager.state in [AppState.RUNNING, AppState.PAUSED]:
                print(f"\n{CLIColors.WARNING}检测到正在运行的任务{CLIColors.ENDC}")
                print("是否停止任务? (y/N): ", end="")
                try:
                    confirm = input().strip().lower()
                    if confirm == 'y':
                        task_controller.stop_task()
                        print(f"{CLIColors.OKGREEN}任务已停止{CLIColors.ENDC}")
                except:
                    pass

def main():
    """主函数"""
    try:
        app = XuanpingCLI()
        app.run()
    except Exception as e:
        print(f"{CLIColors.FAIL}启动CLI应用失败: {e}{CLIColors.ENDC}")
        sys.exit(1)

if __name__ == "__main__":
    main()