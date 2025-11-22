#!/usr/bin/env python3
"""
AI产品选择器错误分析工具
功能：深度分析日志文件，识别和分类错误模式
"""

import os
import re
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter
import argparse

class ErrorAnalyzer:
    """错误分析器"""
    
    def __init__(self):
        self.error_patterns = {
            # 网络相关错误
            'network': [
                r'timeout.*exceeded',
                r'connection.*failed',
                r'network.*error',
                r'unable to connect',
                r'connection refused',
                r'dns.*resolution.*failed',
            ],
            
            # 浏览器相关错误
            'browser': [
                r'playwright.*error',
                r'browser.*crashed',
                r'page.*closed',
                r'navigation.*failed',
                r'element.*not.*found',
                r'selector.*not.*found',
            ],
            
            # 文件系统错误
            'filesystem': [
                r'file.*not.*found',
                r'permission.*denied',
                r'no such file or directory',
                r'cannot.*access',
                r'disk.*full',
                r'invalid.*path',
            ],
            
            # 配置错误
            'configuration': [
                r'config.*error',
                r'invalid.*configuration',
                r'missing.*required.*parameter',
                r'json.*decode.*error',
                r'yaml.*parse.*error',
            ],
            
            # 数据处理错误
            'data_processing': [
                r'excel.*error',
                r'csv.*error',
                r'data.*parsing.*failed',
                r'invalid.*data.*format',
                r'conversion.*error',
            ],
            
            # 内存和资源错误
            'resource': [
                r'out of memory',
                r'memory.*error',
                r'resource.*exhausted',
                r'too many.*open.*files',
                r'segmentation.*fault',
            ],
            
            # 应用逻辑错误
            'logic': [
                r'assertion.*error',
                r'index.*out.*of.*range',
                r'key.*error',
                r'attribute.*error',
                r'type.*error',
                r'value.*error',
            ]
        }
        
        self.severity_keywords = {
            'critical': ['crash', 'fatal', 'emergency', 'segmentation fault', 'out of memory'],
            'high': ['error', 'exception', 'failed', 'timeout'],
            'medium': ['warning', 'warn', 'deprecated'],
            'low': ['info', 'debug', 'notice']
        }
    
    def analyze_log_file(self, log_file: str) -> Dict[str, Any]:
        """分析单个日志文件"""
        if not os.path.exists(log_file):
            return {'error': f'Log file not found: {log_file}'}
        
        with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        lines = content.split('\n')
        
        analysis = {
            'file': log_file,
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'total_lines': len(lines),
                'error_lines': 0,
                'warning_lines': 0,
                'success_lines': 0,
            },
            'errors_by_category': defaultdict(list),
            'errors_by_severity': defaultdict(list),
            'error_timeline': [],
            'frequent_errors': [],
            'recommendations': []
        }
        
        # 分析每一行
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # 统计基本信息
            if 'error' in line_lower:
                analysis['stats']['error_lines'] += 1
            elif 'warning' in line_lower or 'warn' in line_lower:
                analysis['stats']['warning_lines'] += 1
            elif 'success' in line_lower:
                analysis['stats']['success_lines'] += 1
            
            # 分析错误类型
            if 'error' in line_lower or 'failed' in line_lower or 'exception' in line_lower:
                self._categorize_error(line, line_num, analysis)
        
        # 分析频繁错误
        self._analyze_frequent_errors(analysis)
        
        # 生成建议
        self._generate_recommendations(analysis)
        
        return analysis
    
    def _categorize_error(self, line: str, line_num: int, analysis: Dict[str, Any]):
        """对错误进行分类"""
        line_lower = line.lower()
        
        # 按类别分类
        for category, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, line_lower, re.IGNORECASE):
                    analysis['errors_by_category'][category].append({
                        'line_number': line_num,
                        'content': line.strip(),
                        'pattern': pattern
                    })
        
        # 按严重程度分类
        severity = self._determine_severity(line_lower)
        analysis['errors_by_severity'][severity].append({
            'line_number': line_num,
            'content': line.strip()
        })
        
        # 时间线分析
        timestamp_match = re.search(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}', line)
        if timestamp_match:
            analysis['error_timeline'].append({
                'timestamp': timestamp_match.group(),
                'line_number': line_num,
                'content': line.strip()
            })
    
    def _determine_severity(self, line_lower: str) -> str:
        """确定错误严重程度"""
        for severity, keywords in self.severity_keywords.items():
            for keyword in keywords:
                if keyword in line_lower:
                    return severity
        return 'low'
    
    def _analyze_frequent_errors(self, analysis: Dict[str, Any]):
        """分析频繁出现的错误"""
        error_counter = Counter()
        
        for category, errors in analysis['errors_by_category'].items():
            for error in errors:
                # 简化错误信息用于统计
                simplified = re.sub(r'\d+', 'X', error['content'])
                simplified = re.sub(r'[0-9a-f-]{36}', 'UUID', simplified)  # UUID
                simplified = re.sub(r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP', simplified)  # IP地址
                error_counter[simplified] += 1
        
        # 获取最频繁的错误
        analysis['frequent_errors'] = [
            {'pattern': pattern, 'count': count} 
            for pattern, count in error_counter.most_common(10)
        ]
    
    def _generate_recommendations(self, analysis: Dict[str, Any]):
        """生成修复建议"""
        recommendations = []
        
        # 根据错误类别生成建议
        if analysis['errors_by_category']['network']:
            recommendations.append({
                'category': 'network',
                'priority': 'high',
                'suggestion': '检查网络连接和防火墙设置，考虑增加重试机制和超时设置'
            })
        
        if analysis['errors_by_category']['browser']:
            recommendations.append({
                'category': 'browser',
                'priority': 'high',
                'suggestion': '检查浏览器进程状态，清理僵尸进程，更新浏览器驱动版本'
            })
        
        if analysis['errors_by_category']['filesystem']:
            recommendations.append({
                'category': 'filesystem',
                'priority': 'medium',
                'suggestion': '检查文件权限和磁盘空间，验证文件路径的正确性'
            })
        
        if analysis['errors_by_category']['configuration']:
            recommendations.append({
                'category': 'configuration',
                'priority': 'high',
                'suggestion': '验证配置文件格式和必需参数，检查环境变量设置'
            })
        
        if analysis['errors_by_category']['resource']:
            recommendations.append({
                'category': 'resource',
                'priority': 'critical',
                'suggestion': '检查系统资源使用情况，考虑增加内存或优化资源管理'
            })
        
        # 根据严重程度统计生成建议
        critical_count = len(analysis['errors_by_severity']['critical'])
        high_count = len(analysis['errors_by_severity']['high'])
        
        if critical_count > 0:
            recommendations.append({
                'category': 'general',
                'priority': 'critical',
                'suggestion': f'发现{critical_count}个严重错误，建议立即停止生产使用并进行修复'
            })
        
        if high_count > 10:
            recommendations.append({
                'category': 'general',
                'priority': 'high',
                'suggestion': f'发现{high_count}个高级错误，建议优先修复以提高系统稳定性'
            })
        
        analysis['recommendations'] = recommendations
    
    def analyze_directory(self, log_dir: str) -> Dict[str, Any]:
        """分析整个日志目录"""
        if not os.path.exists(log_dir):
            return {'error': f'Directory not found: {log_dir}'}
        
        log_files = []
        for root, dirs, files in os.walk(log_dir):
            for file in files:
                if file.endswith('.log') or file.endswith('.txt'):
                    log_files.append(os.path.join(root, file))
        
        if not log_files:
            return {'error': f'No log files found in: {log_dir}'}
        
        overall_analysis = {
            'directory': log_dir,
            'timestamp': datetime.now().isoformat(),
            'total_files': len(log_files),
            'file_analyses': [],
            'summary': {
                'total_errors': 0,
                'total_warnings': 0,
                'most_common_errors': [],
                'critical_issues': [],
                'overall_recommendations': []
            }
        }
        
        # 分析每个文件
        all_errors = Counter()
        all_recommendations = []
        
        for log_file in log_files:
            file_analysis = self.analyze_log_file(log_file)
            overall_analysis['file_analyses'].append(file_analysis)
            
            # 汇总统计
            overall_analysis['summary']['total_errors'] += file_analysis['stats']['error_lines']
            overall_analysis['summary']['total_warnings'] += file_analysis['stats']['warning_lines']
            
            # 汇总频繁错误
            for error_info in file_analysis['frequent_errors']:
                all_errors[error_info['pattern']] += error_info['count']
            
            # 汇总建议
            all_recommendations.extend(file_analysis['recommendations'])
            
            # 汇总严重问题
            if file_analysis['errors_by_severity']['critical']:
                overall_analysis['summary']['critical_issues'].extend(
                    file_analysis['errors_by_severity']['critical']
                )
        
        # 生成总体统计
        overall_analysis['summary']['most_common_errors'] = [
            {'pattern': pattern, 'count': count}
            for pattern, count in all_errors.most_common(5)
        ]
        
        # 去重和排序建议
        unique_recommendations = {}
        for rec in all_recommendations:
            key = f"{rec['category']}_{rec['priority']}"
            if key not in unique_recommendations or rec['priority'] == 'critical':
                unique_recommendations[key] = rec
        
        overall_analysis['summary']['overall_recommendations'] = list(unique_recommendations.values())
        
        return overall_analysis
    
    def generate_html_report(self, analysis: Dict[str, Any], output_file: str):
        """生成HTML格式的报告"""
        html_template = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>错误分析报告</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1, h2, h3 { color: #333; }
        .stats { display: flex; gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .error-critical { color: #dc3545; }
        .error-high { color: #fd7e14; }
        .error-medium { color: #ffc107; }
        .error-low { color: #28a745; }
        .recommendation { background: #e3f2fd; padding: 10px; margin: 10px 0; border-left: 4px solid #2196f3; border-radius: 4px; }
        .critical-rec { border-left-color: #f44336; background: #ffebee; }
        .high-rec { border-left-color: #ff9800; background: #fff3e0; }
        table { width: 100%; border-collapse: collapse; margin: 20px 0; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
        th { background-color: #f8f9fa; font-weight: bold; }
        .error-line { font-family: monospace; font-size: 0.9em; background: #f8f9fa; padding: 5px; border-radius: 3px; }
        .timeline { max-height: 300px; overflow-y: auto; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 AI产品选择器错误分析报告</h1>
        <p><strong>生成时间:</strong> {timestamp}</p>
        <p><strong>分析文件:</strong> {analyzed_files}</p>
        
        <h2>📊 统计概览</h2>
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number error-critical">{total_errors}</div>
                <div>总错误数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error-medium">{total_warnings}</div>
                <div>总警告数</div>
            </div>
            <div class="stat-card">
                <div class="stat-number error-low">{total_success}</div>
                <div>成功操作</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{total_files}</div>
                <div>分析文件数</div>
            </div>
        </div>
        
        <h2>🚨 严重问题</h2>
        <div id="critical-issues">
            {critical_issues_html}
        </div>
        
        <h2>📈 错误分类统计</h2>
        <table>
            <thead>
                <tr><th>类别</th><th>数量</th><th>占比</th><th>描述</th></tr>
            </thead>
            <tbody>
                {error_categories_html}
            </tbody>
        </table>
        
        <h2>🔥 频繁错误</h2>
        <table>
            <thead>
                <tr><th>错误模式</th><th>出现次数</th></tr>
            </thead>
            <tbody>
                {frequent_errors_html}
            </tbody>
        </table>
        
        <h2>💡 修复建议</h2>
        <div id="recommendations">
            {recommendations_html}
        </div>
        
        <h2>⏱️ 错误时间线</h2>
        <div class="timeline">
            {timeline_html}
        </div>
    </div>
</body>
</html>
        """
        
        # 准备HTML内容
        def format_analysis_for_html(analysis):
            # 统计信息
            if 'summary' in analysis:
                # 目录分析
                stats = analysis['summary']
                total_errors = stats.get('total_errors', 0)
                total_warnings = stats.get('total_warnings', 0)
                total_success = sum(fa['stats']['success_lines'] for fa in analysis['file_analyses'])
                total_files = analysis['total_files']
                analyzed_files = analysis['directory']
                critical_issues = stats.get('critical_issues', [])
                recommendations = stats.get('overall_recommendations', [])
                frequent_errors = stats.get('most_common_errors', [])
                
                # 合并所有文件的错误分类
                all_categories = defaultdict(int)
                for fa in analysis['file_analyses']:
                    for category, errors in fa['errors_by_category'].items():
                        all_categories[category] += len(errors)
                
                timeline = []
                for fa in analysis['file_analyses']:
                    timeline.extend(fa['error_timeline'])
                timeline.sort(key=lambda x: x.get('timestamp', ''))
                
            else:
                # 单文件分析
                stats = analysis['stats']
                total_errors = stats['error_lines']
                total_warnings = stats['warning_lines']
                total_success = stats['success_lines']
                total_files = 1
                analyzed_files = analysis['file']
                critical_issues = analysis['errors_by_severity'].get('critical', [])
                recommendations = analysis['recommendations']
                frequent_errors = analysis['frequent_errors']
                all_categories = {k: len(v) for k, v in analysis['errors_by_category'].items()}
                timeline = analysis['error_timeline']
            
            # 生成HTML片段
            critical_issues_html = ""
            if critical_issues:
                for issue in critical_issues[:10]:  # 限制显示数量
                    critical_issues_html += f'<div class="error-line">Line {issue.get("line_number", "N/A")}: {issue["content"]}</div>'
            else:
                critical_issues_html = "<p>✅ 未发现严重问题</p>"
            
            error_categories_html = ""
            total_cat_errors = sum(all_categories.values())
            for category, count in sorted(all_categories.items(), key=lambda x: x[1], reverse=True):
                percentage = (count / total_cat_errors * 100) if total_cat_errors > 0 else 0
                error_categories_html += f"""
                <tr>
                    <td>{category}</td>
                    <td>{count}</td>
                    <td>{percentage:.1f}%</td>
                    <td>{self._get_category_description(category)}</td>
                </tr>
                """
            
            frequent_errors_html = ""
            for error in frequent_errors[:10]:
                pattern = error['pattern'][:100] + "..." if len(error['pattern']) > 100 else error['pattern']
                frequent_errors_html += f'<tr><td class="error-line">{pattern}</td><td>{error["count"]}</td></tr>'
            
            recommendations_html = ""
            for rec in recommendations:
                rec_class = f"{rec['priority']}-rec" if rec['priority'] in ['critical', 'high'] else 'recommendation'
                recommendations_html += f"""
                <div class="recommendation {rec_class}">
                    <strong>[{rec['priority'].upper()}] {rec['category']}</strong><br>
                    {rec['suggestion']}
                </div>
                """
            
            timeline_html = ""
            for event in timeline[-20:]:  # 显示最近的20个事件
                timeline_html += f"""
                <div class="error-line">
                    {event.get('timestamp', 'N/A')} - Line {event.get('line_number', 'N/A')}: {event['content'][:150]}...
                </div>
                """
            
            return {
                'timestamp': analysis.get('timestamp', datetime.now().isoformat()),
                'analyzed_files': analyzed_files,
                'total_errors': total_errors,
                'total_warnings': total_warnings,
                'total_success': total_success,
                'total_files': total_files,
                'critical_issues_html': critical_issues_html,
                'error_categories_html': error_categories_html,
                'frequent_errors_html': frequent_errors_html,
                'recommendations_html': recommendations_html,
                'timeline_html': timeline_html
            }
        
        html_data = format_analysis_for_html(analysis)
        html_content = html_template.format(**html_data)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
    
    def _get_category_description(self, category: str) -> str:
        """获取错误类别描述"""
        descriptions = {
            'network': '网络连接和通信相关错误',
            'browser': '浏览器和页面操作相关错误',
            'filesystem': '文件系统和磁盘操作错误',
            'configuration': '配置文件和参数设置错误',
            'data_processing': '数据处理和格式转换错误',
            'resource': '系统资源和内存相关错误',
            'logic': '程序逻辑和代码执行错误'
        }
        return descriptions.get(category, '其他类型错误')

def main():
    parser = argparse.ArgumentParser(description='AI产品选择器错误分析工具')
    parser.add_argument('input', help='日志文件或目录路径')
    parser.add_argument('--output', '-o', help='输出文件路径（JSON格式）')
    parser.add_argument('--html', help='生成HTML报告文件路径')
    parser.add_argument('--format', choices=['json', 'text'], default='text', help='输出格式')
    
    args = parser.parse_args()
    
    analyzer = ErrorAnalyzer()
    
    # 分析输入
    if os.path.isdir(args.input):
        analysis = analyzer.analyze_directory(args.input)
    else:
        analysis = analyzer.analyze_log_file(args.input)
    
    # 输出结果
    if args.format == 'json' or args.output:
        output_file = args.output or 'error_analysis.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis, f, indent=2, ensure_ascii=False)
        print(f"JSON报告已保存到: {output_file}")
    
    if args.html:
        analyzer.generate_html_report(analysis, args.html)
        print(f"HTML报告已保存到: {args.html}")
    
    if args.format == 'text':
        # 输出简要文本报告
        if 'summary' in analysis:
            print(f"\n📋 错误分析汇总报告")
            print(f"分析目录: {analysis['directory']}")
            print(f"分析文件: {analysis['total_files']} 个")
            print(f"总错误数: {analysis['summary']['total_errors']}")
            print(f"总警告数: {analysis['summary']['total_warnings']}")
            print(f"严重问题: {len(analysis['summary']['critical_issues'])} 个")
            
            if analysis['summary']['most_common_errors']:
                print(f"\n🔥 最频繁的错误:")
                for i, error in enumerate(analysis['summary']['most_common_errors'][:3], 1):
                    print(f"  {i}. {error['pattern'][:80]}... (出现{error['count']}次)")
            
            if analysis['summary']['overall_recommendations']:
                print(f"\n💡 主要建议:")
                for rec in analysis['summary']['overall_recommendations'][:3]:
                    print(f"  [{rec['priority'].upper()}] {rec['suggestion']}")
        
        else:
            print(f"\n📋 错误分析报告")
            print(f"分析文件: {analysis['file']}")
            print(f"总行数: {analysis['stats']['total_lines']}")
            print(f"错误行: {analysis['stats']['error_lines']}")
            print(f"警告行: {analysis['stats']['warning_lines']}")
            print(f"成功行: {analysis['stats']['success_lines']}")
            
            if analysis['frequent_errors']:
                print(f"\n🔥 频繁错误:")
                for error in analysis['frequent_errors'][:3]:
                    print(f"  - {error['pattern'][:80]}... (出现{error['count']}次)")
            
            if analysis['recommendations']:
                print(f"\n💡 修复建议:")
                for rec in analysis['recommendations'][:3]:
                    print(f"  [{rec['priority'].upper()}] {rec['suggestion']}")

if __name__ == '__main__':
    main()
