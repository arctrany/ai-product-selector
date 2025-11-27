"""
测试数据打印工具

为集成测试提供统一的数据打印功能，支持多种格式和配置选项。
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime

class PrintFormat(Enum):
    """打印格式枚举"""
    JSON = "json"
    TABLE = "table"
    COMPACT = "compact"

class PrintLevel(Enum):
    """打印级别枚举"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class PrintConfig:
    """打印配置"""
    enabled: bool = True
    format: PrintFormat = PrintFormat.TABLE
    level: PrintLevel = PrintLevel.INFO
    max_rows: int = 50
    show_raw_data: bool = False
    show_formatted_data: bool = True
    color_output: bool = True
    indent_size: int = 2
    truncate_length: int = 100

class TestDataPrinter:
    """测试数据打印器"""
    
    def __init__(self, config: Optional[PrintConfig] = None, logger: Optional[logging.Logger] = None):
        """
        初始化打印器
        
        Args:
            config: 打印配置
            logger: 日志记录器
        """
        self.config = config or PrintConfig()
        self.logger = logger or logging.getLogger(__name__)
        self._printed_sections = set()
    
    def print_test_case_data(self, 
                           test_case_id: str,
                           test_case_name: str,
                           data: Dict[str, Any],
                           section: str = "default") -> None:
        """
        打印测试用例数据
        
        Args:
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            data: 要打印的数据
            section: 数据部分标识
        """
        if not self.config.enabled:
            return
            
        # 避免重复打印相同部分
        section_key = f"{test_case_id}_{section}"
        if section_key in self._printed_sections:
            return
        self._printed_sections.add(section_key)
        
        try:
            # 添加测试用例标识
            header = f"[测试用例: {test_case_name} ({test_case_id})]"
            
            if self.config.format == PrintFormat.JSON:
                self._print_json_format(header, data)
            elif self.config.format == PrintFormat.TABLE:
                self._print_table_format(header, data)
            elif self.config.format == PrintFormat.COMPACT:
                self._print_compact_format(header, data)
                
        except Exception as e:
            self.logger.error(f"打印测试数据时出错: {e}")
    
    def print_scraping_result(self,
                            test_case_id: str,
                            test_case_name: str,
                            result: Any,
                            section: str = "scraping_result") -> None:
        """
        打印抓取结果
        
        Args:
            test_case_id: 测试用例ID
            test_case_name: 测试用例名称
            result: 抓取结果对象
            section: 数据部分标识
        """
        if not self.config.enabled:
            return
            
        try:
            # 转换结果为字典格式
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            elif hasattr(result, '__dict__'):
                result_dict = result.__dict__
            else:
                result_dict = {'data': result}
                
            self.print_test_case_data(test_case_id, test_case_name, result_dict, section)
            
        except Exception as e:
            self.logger.error(f"打印抓取结果时出错: {e}")
    
    def _print_json_format(self, header: str, data: Dict[str, Any]) -> None:
        """打印JSON格式数据"""
        try:
            # 处理大量数据
            processed_data = self._process_large_data(data)
            
            # 格式化输出
            json_str = json.dumps(processed_data, ensure_ascii=False, indent=self.config.indent_size)
            
            # 截断过长的输出
            if len(json_str) > 5000:  # 限制5KB
                json_str = json_str[:5000] + "... (truncated)"
            
            # 使用日志系统输出
            log_msg = f"{header}\n{json_str}"
            self._log_message(log_msg, self.config.level)
            
        except Exception as e:
            self.logger.error(f"JSON格式打印出错: {e}")
    
    def _print_table_format(self, header: str, data: Dict[str, Any]) -> None:
        """打印表格格式数据"""
        try:
            # 处理大量数据
            processed_data = self._process_large_data(data)
            
            # 构建表格
            table_lines = [header, "=" * 80]
            
            # 分离原始数据和格式化数据
            raw_data = {}
            formatted_data = {}
            
            if 'data' in processed_data and isinstance(processed_data['data'], dict):
                raw_data = processed_data['data']
                if 'formatted' in raw_data:
                    formatted_data = raw_data.pop('formatted', {})
            
            # 打印原始数据
            if self.config.show_raw_data and raw_data:
                table_lines.append("原始数据:")
                table_lines.append("-" * 40)
                for key, value in self._truncate_dict(raw_data).items():
                    table_lines.append(f"{key:<25} : {self._format_value(value)}")
                table_lines.append("")
            
            # 打印格式化数据
            if self.config.show_formatted_data and formatted_data:
                table_lines.append("格式化数据:")
                table_lines.append("-" * 40)
                for key, value in self._truncate_dict(formatted_data).items():
                    table_lines.append(f"{key:<25} : {self._format_value(value)}")
                table_lines.append("")
            
            # 打印其他字段
            other_fields = {k: v for k, v in processed_data.items() if k not in ['data']}
            if other_fields:
                table_lines.append("其他信息:")
                table_lines.append("-" * 40)
                for key, value in self._truncate_dict(other_fields).items():
                    table_lines.append(f"{key:<25} : {self._format_value(value)}")
            
            # 输出表格
            table_output = "\n".join(table_lines)
            self._log_message(table_output, self.config.level)
            
        except Exception as e:
            self.logger.error(f"表格格式打印出错: {e}")
    
    def _print_compact_format(self, header: str, data: Dict[str, Any]) -> None:
        """打印紧凑格式数据"""
        try:
            # 处理大量数据
            processed_data = self._process_large_data(data)
            
            # 构建紧凑输出
            compact_lines = [header]
            
            # 提取关键字段
            key_fields = self._extract_key_fields(processed_data)
            if key_fields:
                compact_lines.append("关键数据: " + ", ".join([
                    f"{k}={self._format_value(v)}" for k, v in key_fields.items()
                ]))
            
            # 添加数据概要
            summary = self._generate_summary(processed_data)
            if summary:
                compact_lines.append(f"数据概要: {summary}")
            
            # 输出紧凑格式
            compact_output = " | ".join(compact_lines)
            self._log_message(compact_output, self.config.level)
            
        except Exception as e:
            self.logger.error(f"紧凑格式打印出错: {e}")
    
    def _process_large_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """处理大量数据"""
        if not isinstance(data, dict):
            return data
            
        processed = {}
        count = 0
        
        for key, value in data.items():
            if count >= self.config.max_rows:
                processed[f"... (剩余{len(data) - count}项已省略)"] = ""
                break
                
            # 处理嵌套字典
            if isinstance(value, dict):
                processed[key] = self._process_large_data(value)
            # 处理列表
            elif isinstance(value, list):
                if len(value) > 10:  # 限制列表长度
                    processed[key] = value[:10] + [f"... (剩余{len(value) - 10}项已省略)"]
                else:
                    processed[key] = value
            else:
                processed[key] = value
                
            count += 1
            
        return processed
    
    def _truncate_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """截断字典中的长值"""
        truncated = {}
        for key, value in data.items():
            truncated[key] = self._truncate_value(value)
        return truncated
    
    def _truncate_value(self, value: Any) -> Any:
        """截断长值"""
        if isinstance(value, str) and len(value) > self.config.truncate_length:
            return value[:self.config.truncate_length] + "..."
        return value
    
    def _format_value(self, value: Any) -> str:
        """格式化值用于显示"""
        if value is None:
            return "None"
        elif isinstance(value, bool):
            return str(value).lower()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, str):
            return self._truncate_value(value)
        elif isinstance(value, (list, tuple)):
            if len(value) > 5:
                return f"[{', '.join(map(str, value[:5]))}, ... ({len(value)} items)]"
            else:
                return str(value)
        elif isinstance(value, dict):
            return f"{{ {len(value)} fields }}"
        else:
            return str(type(value).__name__)
    
    def _extract_key_fields(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """提取关键字段"""
        key_fields = {}
        
        # 定义关键字段
        important_keys = [
            'success', 'error_message', 'execution_time', 'status',
            'category', 'sku', 'brand_name', 'monthly_sales_volume',
            'monthly_sales_amount', 'daily_sales_volume', 'daily_sales_amount'
        ]
        
        # 从数据中提取关键字段
        def extract_from_dict(d, prefix=""):
            for key, value in d.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if key in important_keys:
                    key_fields[key] = value
                elif isinstance(value, dict):
                    extract_from_dict(value, full_key)
        
        if isinstance(data, dict):
            extract_from_dict(data)
            
        return key_fields
    
    def _generate_summary(self, data: Dict[str, Any]) -> str:
        """生成数据概要"""
        try:
            summary_parts = []
            
            # 成功状态
            if 'success' in data:
                summary_parts.append(f"成功: {data['success']}")
            
            # 执行时间
            if 'execution_time' in data:
                summary_parts.append(f"耗时: {data['execution_time']:.2f}s")
            
            # 数据字段数
            if 'data' in data and isinstance(data['data'], dict):
                summary_parts.append(f"字段数: {len(data['data'])}")
                
            return ", ".join(summary_parts)
        except Exception:
            return "无法生成概要"
    
    def _log_message(self, message: str, level: PrintLevel) -> None:
        """记录消息到日志"""
        try:
            # 根据配置级别记录日志
            if level == PrintLevel.DEBUG:
                self.logger.debug(message)
            elif level == PrintLevel.INFO:
                self.logger.info(message)
            elif level == PrintLevel.WARNING:
                self.logger.warning(message)
            elif level == PrintLevel.ERROR:
                self.logger.error(message)
            else:
                self.logger.info(message)
                
        except Exception as e:
            # 如果日志记录失败，回退到print
            print(f"[Fallback Print] {message}")

# 全局默认打印器实例
default_printer = TestDataPrinter()

def print_test_data(test_case_id: str,
                   test_case_name: str,
                   data: Dict[str, Any],
                   section: str = "default",
                   config: Optional[PrintConfig] = None) -> None:
    """
    打印测试数据的便捷函数
    
    Args:
        test_case_id: 测试用例ID
        test_case_name: 测试用例名称
        data: 要打印的数据
        section: 数据部分标识
        config: 打印配置
    """
    printer = TestDataPrinter(config) if config else default_printer
    printer.print_test_case_data(test_case_id, test_case_name, data, section)

def print_scraping_result(test_case_id: str,
                         test_case_name: str,
                         result: Any,
                         section: str = "scraping_result",
                         config: Optional[PrintConfig] = None) -> None:
    """
    打印抓取结果的便捷函数
    
    Args:
        test_case_id: 测试用例ID
        test_case_name: 测试用例名称
        result: 抓取结果对象
        section: 数据部分标识
        config: 打印配置
    """
    printer = TestDataPrinter(config) if config else default_printer
    printer.print_scraping_result(test_case_id, test_case_name, result, section)
