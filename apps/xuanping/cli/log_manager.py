"""
日志管理器

负责日志的导出、格式化等操作
"""

import json
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

from apps.xuanping.cli.models import LogEntry
from apps.xuanping.common.logging_config import xuanping_logger

class LogExportFormat(Enum):
    """日志导出格式"""
    TXT = "txt"
    CSV = "csv"
    JSON = "json"
    HTML = "html"

class LogManager:
    """日志管理器"""
    
    def __init__(self):
        self.log_dir = xuanping_logger.get_log_directory()

    def get_recent_logs(self, limit: int = 100, level_filter: Optional[str] = None) -> List[LogEntry]:
        """从日志文件中读取最近的日志条目"""
        logs = []

        # 获取所有日志文件，按修改时间排序
        log_files = xuanping_logger.list_log_files()

        for log_file_info in log_files:
            try:
                with open(log_file_info['path'], 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                # 从文件末尾开始读取
                for line in reversed(lines):
                    line = line.strip()
                    if not line:
                        continue

                    # 解析日志行
                    log_entry = self._parse_log_line(line)
                    if log_entry:
                        # 应用级别过滤
                        if level_filter and log_entry.level.value.lower() != level_filter.lower():
                            continue

                        logs.append(log_entry)

                        # 达到限制数量就停止
                        if len(logs) >= limit:
                            break

                # 如果已经收集够了日志就停止读取其他文件
                if len(logs) >= limit:
                    break

            except Exception as e:
                print(f"读取日志文件失败 {log_file_info['name']}: {e}")
                continue

        # 按时间排序（最新的在前）
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]

    def _parse_log_line(self, line: str) -> Optional[LogEntry]:
        """解析日志行"""
        try:
            # 日志格式: 2025-11-06 13:48:00 - xuanping - INFO - 消息内容
            pattern = r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (.*?) - (DEBUG|INFO|WARNING|ERROR) - (.*)$'
            match = re.match(pattern, line)

            if match:
                timestamp_str, logger_name, level_str, message = match.groups()
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')

                # 从消息中提取店铺ID和步骤信息（如果有）
                store_id = None
                step = None

                # 尝试提取店铺ID
                store_match = re.search(r'店铺.*?(\d+)', message)
                if store_match:
                    store_id = store_match.group(1)

                # 尝试提取步骤信息
                step_match = re.search(r'处理店铺|步骤|阶段', message)
                if step_match:
                    step = step_match.group(0)

                from apps.xuanping.cli.models import LogLevel
                level_map = {
                    'DEBUG': LogLevel.DEBUG,
                    'INFO': LogLevel.INFO,
                    'WARNING': LogLevel.WARNING,
                    'ERROR': LogLevel.ERROR
                }

                return LogEntry(
                    timestamp=timestamp,
                    level=level_map.get(level_str, LogLevel.INFO),
                    message=message,
                    store_id=store_id,
                    step=step
                )
        except Exception:
            pass

        return None

    def export_logs_txt(self, filename: str, level_filter: Optional[str] = None) -> bool:
        """导出日志为TXT格式"""
        logs = self.get_recent_logs(limit=10000, level_filter=level_filter)
        return self.export_logs(logs, filename, LogExportFormat.TXT)

    def export_logs_csv(self, filename: str, level_filter: Optional[str] = None) -> bool:
        """导出日志为CSV格式"""
        logs = self.get_recent_logs(limit=10000, level_filter=level_filter)
        return self.export_logs(logs, filename, LogExportFormat.CSV)

    def export_logs_json(self, filename: str, level_filter: Optional[str] = None) -> bool:
        """导出日志为JSON格式"""
        logs = self.get_recent_logs(limit=10000, level_filter=level_filter)
        return self.export_logs(logs, filename, LogExportFormat.JSON)

    def export_logs_html(self, filename: str, level_filter: Optional[str] = None) -> bool:
        """导出日志为HTML格式"""
        logs = self.get_recent_logs(limit=10000, level_filter=level_filter)
        return self.export_logs(logs, filename, LogExportFormat.HTML)

    def export_logs(self, logs: List[LogEntry], filename: str, format_type: LogExportFormat) -> bool:
        """导出日志到文件"""
        try:
            filepath = Path(filename)
            filepath.parent.mkdir(parents=True, exist_ok=True)
            
            if format_type == LogExportFormat.TXT:
                return self._export_txt(logs, filepath)
            elif format_type == LogExportFormat.CSV:
                return self._export_csv(logs, filepath)
            elif format_type == LogExportFormat.JSON:
                return self._export_json(logs, filepath)
            elif format_type == LogExportFormat.HTML:
                return self._export_html(logs, filepath)
            else:
                return False
                
        except Exception as e:
            print(f"导出日志失败: {e}")
            return False
    
    def _export_txt(self, logs: List[LogEntry], filepath: Path) -> bool:
        """导出为TXT格式"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write("智能选品系统日志\n")
                f.write("=" * 50 + "\n")
                f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"日志条数: {len(logs)}\n")
                f.write("=" * 50 + "\n\n")
                
                for log in logs:
                    timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    level = log.level.value.upper()
                    message = log.message
                    
                    f.write(f"[{timestamp}] [{level}] {message}\n")
                    
                    if log.store_id:
                        f.write(f"  店铺ID: {log.store_id}\n")
                    if log.step:
                        f.write(f"  步骤: {log.step}\n")
                    f.write("\n")
            
            return True
        except Exception as e:
            print(f"导出TXT格式失败: {e}")
            return False
    
    def _export_csv(self, logs: List[LogEntry], filepath: Path) -> bool:
        """导出为CSV格式"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                
                # 写入标题行
                writer.writerow(['时间戳', '级别', '消息', '店铺ID', '步骤'])
                
                # 写入日志数据
                for log in logs:
                    writer.writerow([
                        log.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
                        log.level.value.upper(),
                        log.message,
                        log.store_id or '',
                        log.step or ''
                    ])
            
            return True
        except Exception as e:
            print(f"导出CSV格式失败: {e}")
            return False
    
    def _export_json(self, logs: List[LogEntry], filepath: Path) -> bool:
        """导出为JSON格式"""
        try:
            log_data = {
                'export_time': datetime.now().isoformat(),
                'total_logs': len(logs),
                'logs': [log.to_dict() for log in logs]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(log_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            print(f"导出JSON格式失败: {e}")
            return False
    
    def _export_html(self, logs: List[LogEntry], filepath: Path) -> bool:
        """导出为HTML格式"""
        try:
            html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>智能选品系统日志</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background-color: #f5f5f5; padding: 10px; border-radius: 5px; margin-bottom: 20px; }}
        .log-entry {{ margin-bottom: 10px; padding: 10px; border-left: 4px solid #ddd; }}
        .log-info {{ border-left-color: #007bff; }}
        .log-warning {{ border-left-color: #ffc107; }}
        .log-error {{ border-left-color: #dc3545; }}
        .log-success {{ border-left-color: #28a745; }}
        .timestamp {{ color: #666; font-size: 0.9em; }}
        .level {{ font-weight: bold; margin-right: 10px; }}
        .message {{ margin-top: 5px; }}
        .details {{ font-size: 0.9em; color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>智能选品系统日志</h1>
        <p>导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>日志条数: {len(logs)}</p>
    </div>
    
    <div class="logs">
"""
            
            for log in logs:
                level_class = f"log-{log.level.value}"
                timestamp = log.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                level = log.level.value.upper()
                
                html_content += f"""
        <div class="log-entry {level_class}">
            <div class="timestamp">{timestamp}</div>
            <div class="level">[{level}]</div>
            <div class="message">{log.message}</div>
"""
                
                if log.store_id or log.step:
                    html_content += '            <div class="details">'
                    if log.store_id:
                        html_content += f'店铺ID: {log.store_id} '
                    if log.step:
                        html_content += f'步骤: {log.step}'
                    html_content += '</div>\n'
                
                html_content += '        </div>\n'
            
            html_content += """
    </div>
</body>
</html>
"""
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            return True
        except Exception as e:
            print(f"导出HTML格式失败: {e}")
            return False

# 全局日志管理器实例
log_manager = LogManager()