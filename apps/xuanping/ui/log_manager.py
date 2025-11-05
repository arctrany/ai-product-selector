"""
日志管理和导出功能

提供日志的过滤、搜索、导出和管理功能
"""

import csv
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from enum import Enum

from .models import LogEntry, LogLevel


class LogExportFormat(Enum):
    """日志导出格式"""
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    HTML = "html"


class LogFilter:
    """日志过滤器"""
    
    def __init__(self):
        self.level_filter: Optional[LogLevel] = None
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.store_id_filter: Optional[str] = None
        self.step_filter: Optional[str] = None
        self.keyword_filter: Optional[str] = None
    
    def matches(self, log_entry: LogEntry) -> bool:
        """检查日志条目是否匹配过滤条件"""
        # 级别过滤
        if self.level_filter and log_entry.level != self.level_filter:
            return False
        
        # 时间过滤
        if self.start_time and log_entry.timestamp < self.start_time:
            return False
        if self.end_time and log_entry.timestamp > self.end_time:
            return False
        
        # 店铺ID过滤
        if self.store_id_filter and log_entry.store_id != self.store_id_filter:
            return False
        
        # 步骤过滤
        if self.step_filter and log_entry.step != self.step_filter:
            return False
        
        # 关键词过滤
        if self.keyword_filter:
            keyword = self.keyword_filter.lower()
            if keyword not in log_entry.message.lower():
                return False
        
        return True


class LogManager:
    """日志管理器"""
    
    def __init__(self, logs_dir: Optional[str] = None):
        """
        初始化日志管理器
        
        Args:
            logs_dir: 日志文件存储目录，默认为用户目录下的.xuanping/logs
        """
        if logs_dir is None:
            home_dir = Path.home()
            self.logs_dir = home_dir / ".xuanping" / "logs"
        else:
            self.logs_dir = Path(logs_dir)
        
        # 确保日志目录存在
        self.logs_dir.mkdir(parents=True, exist_ok=True)
    
    def filter_logs(self, logs: List[LogEntry], log_filter: LogFilter) -> List[LogEntry]:
        """
        根据过滤条件过滤日志
        
        Args:
            logs: 日志列表
            log_filter: 过滤条件
            
        Returns:
            List[LogEntry]: 过滤后的日志列表
        """
        return [log for log in logs if log_filter.matches(log)]
    
    def search_logs(self, logs: List[LogEntry], keyword: str) -> List[LogEntry]:
        """
        在日志中搜索关键词
        
        Args:
            logs: 日志列表
            keyword: 搜索关键词
            
        Returns:
            List[LogEntry]: 包含关键词的日志列表
        """
        keyword_lower = keyword.lower()
        return [
            log for log in logs 
            if keyword_lower in log.message.lower() or 
               (log.store_id and keyword_lower in log.store_id.lower()) or
               (log.step and keyword_lower in log.step.lower())
        ]
    
    def get_logs_by_level(self, logs: List[LogEntry], level: LogLevel) -> List[LogEntry]:
        """
        获取指定级别的日志
        
        Args:
            logs: 日志列表
            level: 日志级别
            
        Returns:
            List[LogEntry]: 指定级别的日志列表
        """
        return [log for log in logs if log.level == level]
    
    def get_logs_by_time_range(self, logs: List[LogEntry], 
                              start_time: datetime, 
                              end_time: datetime) -> List[LogEntry]:
        """
        获取指定时间范围内的日志
        
        Args:
            logs: 日志列表
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            List[LogEntry]: 时间范围内的日志列表
        """
        return [
            log for log in logs 
            if start_time <= log.timestamp <= end_time
        ]
    
    def get_recent_logs(self, logs: List[LogEntry], hours: int = 1) -> List[LogEntry]:
        """
        获取最近指定小时数的日志
        
        Args:
            logs: 日志列表
            hours: 小时数
            
        Returns:
            List[LogEntry]: 最近的日志列表
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return [log for log in logs if log.timestamp >= cutoff_time]
    
    def export_logs(self, logs: List[LogEntry], 
                   export_path: str, 
                   format_type: LogExportFormat = LogExportFormat.TXT) -> bool:
        """
        导出日志到文件
        
        Args:
            logs: 要导出的日志列表
            export_path: 导出文件路径
            format_type: 导出格式
            
        Returns:
            bool: 导出是否成功
        """
        try:
            export_path = Path(export_path)
            
            if format_type == LogExportFormat.TXT:
                return self._export_to_txt(logs, export_path)
            elif format_type == LogExportFormat.CSV:
                return self._export_to_csv(logs, export_path)
            elif format_type == LogExportFormat.JSON:
                return self._export_to_json(logs, export_path)
            elif format_type == LogExportFormat.HTML:
                return self._export_to_html(logs, export_path)
            else:
                return False
                
        except Exception as e:
            print(f"导出日志失败: {e}")
            return False
    
    def _export_to_txt(self, logs: List[LogEntry], export_path: Path) -> bool:
        """导出为文本格式"""
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("智能选品系统日志\n")
                f.write("=" * 50 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"日志条数: {len(logs)}\n")
                f.write("=" * 50 + "\n\n")
                
                for log in logs:
                    timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    level_str = log.level.value.upper()
                    
                    f.write(f"[{timestamp_str}] [{level_str}] {log.message}")
                    
                    if log.store_id:
                        f.write(f" (店铺: {log.store_id})")
                    if log.step:
                        f.write(f" (步骤: {log.step})")
                    
                    f.write("\n")
            
            return True
            
        except Exception as e:
            print(f"导出TXT格式失败: {e}")
            return False
    
    def _export_to_csv(self, logs: List[LogEntry], export_path: Path) -> bool:
        """导出为CSV格式"""
        try:
            with open(export_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入表头
                writer.writerow(['时间', '级别', '消息', '店铺ID', '步骤'])
                
                # 写入数据
                for log in logs:
                    writer.writerow([
                        log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        log.level.value,
                        log.message,
                        log.store_id or '',
                        log.step or ''
                    ])
            
            return True
            
        except Exception as e:
            print(f"导出CSV格式失败: {e}")
            return False
    
    def _export_to_json(self, logs: List[LogEntry], export_path: Path) -> bool:
        """导出为JSON格式"""
        try:
            export_data = {
                'export_info': {
                    'export_time': datetime.now().isoformat(),
                    'total_logs': len(logs),
                    'format': 'json'
                },
                'logs': [log.to_dict() for log in logs]
            }
            
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出JSON格式失败: {e}")
            return False
    
    def _export_to_html(self, logs: List[LogEntry], export_path: Path) -> bool:
        """导出为HTML格式"""
        try:
            html_content = self._generate_html_content(logs)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
            
        except Exception as e:
            print(f"导出HTML格式失败: {e}")
            return False
    
    def _generate_html_content(self, logs: List[LogEntry]) -> str:
        """生成HTML内容"""
        html = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能选品系统日志</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .log-container {
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .log-entry {
            padding: 12px 20px;
            border-bottom: 1px solid #eee;
            display: flex;
            align-items: flex-start;
            gap: 15px;
        }
        .log-entry:last-child {
            border-bottom: none;
        }
        .log-entry:hover {
            background-color: #f8f9fa;
        }
        .log-timestamp {
            color: #666;
            font-size: 12px;
            min-width: 140px;
            font-family: monospace;
        }
        .log-level {
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            min-width: 60px;
            text-align: center;
        }
        .log-level.info {
            background-color: #e3f2fd;
            color: #1976d2;
        }
        .log-level.warning {
            background-color: #fff3e0;
            color: #f57c00;
        }
        .log-level.error {
            background-color: #ffebee;
            color: #d32f2f;
        }
        .log-level.success {
            background-color: #e8f5e8;
            color: #388e3c;
        }
        .log-message {
            flex: 1;
            line-height: 1.4;
        }
        .log-meta {
            color: #888;
            font-size: 11px;
            margin-top: 4px;
        }
        .stats {
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
        }
        .stat-item {
            text-align: center;
        }
        .stat-value {
            font-size: 24px;
            font-weight: bold;
            color: #333;
        }
        .stat-label {
            color: #666;
            font-size: 12px;
            margin-top: 4px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 智能选品系统日志</h1>
        <p>导出时间: {export_time} | 总计 {total_logs} 条日志</p>
    </div>
    
    <div class="stats">
        <div class="stats-grid">
            <div class="stat-item">
                <div class="stat-value">{info_count}</div>
                <div class="stat-label">信息</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{warning_count}</div>
                <div class="stat-label">警告</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{error_count}</div>
                <div class="stat-label">错误</div>
            </div>
            <div class="stat-item">
                <div class="stat-value">{success_count}</div>
                <div class="stat-label">成功</div>
            </div>
        </div>
    </div>
    
    <div class="log-container">
        {log_entries}
    </div>
</body>
</html>"""
        
        # 统计各级别日志数量
        level_counts = {level: 0 for level in LogLevel}
        for log in logs:
            level_counts[log.level] += 1
        
        # 生成日志条目HTML
        log_entries_html = ""
        for log in logs:
            timestamp_str = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
            level_class = log.level.value.lower()
            level_display = log.level.value.upper()
            
            meta_info = []
            if log.store_id:
                meta_info.append(f"店铺: {log.store_id}")
            if log.step:
                meta_info.append(f"步骤: {log.step}")
            
            meta_html = ""
            if meta_info:
                meta_html = f'<div class="log-meta">{" | ".join(meta_info)}</div>'
            
            log_entries_html += f"""
        <div class="log-entry">
            <div class="log-timestamp">{timestamp_str}</div>
            <div class="log-level {level_class}">{level_display}</div>
            <div class="log-message">
                {log.message}
                {meta_html}
            </div>
        </div>"""
        
        # 填充模板
        return html.format(
            export_time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_logs=len(logs),
            info_count=level_counts[LogLevel.INFO],
            warning_count=level_counts[LogLevel.WARNING],
            error_count=level_counts[LogLevel.ERROR],
            success_count=level_counts[LogLevel.SUCCESS],
            log_entries=log_entries_html
        )
    
    def get_log_statistics(self, logs: List[LogEntry]) -> Dict[str, Any]:
        """
        获取日志统计信息
        
        Args:
            logs: 日志列表
            
        Returns:
            Dict[str, Any]: 统计信息
        """
        if not logs:
            return {
                'total_count': 0,
                'level_counts': {level.value: 0 for level in LogLevel},
                'time_range': None,
                'store_count': 0,
                'step_count': 0
            }
        
        # 统计各级别数量
        level_counts = {level.value: 0 for level in LogLevel}
        for log in logs:
            level_counts[log.level.value] += 1
        
        # 时间范围
        timestamps = [log.timestamp for log in logs]
        time_range = {
            'start': min(timestamps),
            'end': max(timestamps),
            'duration': max(timestamps) - min(timestamps)
        }
        
        # 店铺和步骤统计
        stores = set(log.store_id for log in logs if log.store_id)
        steps = set(log.step for log in logs if log.step)
        
        return {
            'total_count': len(logs),
            'level_counts': level_counts,
            'time_range': time_range,
            'store_count': len(stores),
            'step_count': len(steps),
            'stores': list(stores),
            'steps': list(steps)
        }
    
    def auto_export_logs(self, logs: List[LogEntry], 
                        base_filename: Optional[str] = None) -> str:
        """
        自动导出日志（使用时间戳作为文件名）
        
        Args:
            logs: 日志列表
            base_filename: 基础文件名，默认使用时间戳
            
        Returns:
            str: 导出文件路径
        """
        if base_filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_filename = f"xuanping_logs_{timestamp}"
        
        export_path = self.logs_dir / f"{base_filename}.txt"
        
        if self.export_logs(logs, str(export_path), LogExportFormat.TXT):
            return str(export_path)
        else:
            raise Exception("自动导出日志失败")


# 全局日志管理器实例
log_manager = LogManager()