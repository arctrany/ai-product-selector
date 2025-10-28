#!/usr/bin/env python3
"""
Flow1 Excel文件提交测试程序
测试使用Excel文件作为表单参数执行flow1工作流
"""

import json
import sys
import time
import base64
import os
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

class Flow1ExcelTest:
    def __init__(self, base_url: str = "http://localhost:8889"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.excel_file_path = "/Users/haowu/IdeaProjects/ai-product-selector3/docs/好店推荐10.xlsx"

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })

    def check_excel_file(self) -> bool:
        """检查Excel文件是否存在"""
        try:
            if os.path.exists(self.excel_file_path):
                file_size = os.path.getsize(self.excel_file_path)
                self.log_test("Excel File Check", True, 
                             f"File exists: {self.excel_file_path} ({file_size} bytes)")
                return True
            else:
                self.log_test("Excel File Check", False, 
                             f"File not found: {self.excel_file_path}")
                return False
        except Exception as e:
            self.log_test("Excel File Check", False, f"Error: {str(e)}")
            return False

    def prepare_excel_file_data(self) -> Optional[Dict[str, Any]]:
        """准备Excel文件数据用于表单提交"""
        try:
            with open(self.excel_file_path, 'rb') as f:
                file_content = f.read()
            
            # 将文件内容编码为base64
            file_content_b64 = base64.b64encode(file_content).decode('utf-8')
            
            # 准备文件数据结构（模拟FastAPI的文件上传格式）
            file_data = {
                "filename": "好店推荐10.xlsx",
                "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "content": file_content_b64,
                "size": len(file_content)
            }
            
            self.log_test("Excel File Preparation", True, 
                         f"Prepared file data: {file_data['filename']} ({file_data['size']} bytes)")
            return file_data
            
        except Exception as e:
            self.log_test("Excel File Preparation", False, f"Error: {str(e)}")
            return None

    def test_server_health(self) -> bool:
        """测试服务器健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            if response.status_code == 200:
                self.log_test("Server Health Check", True, "Server is running")
                return True
            else:
                self.log_test("Server Health Check", False, 
                             f"HTTP {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.log_test("Server Health Check", False, f"Connection error: {str(e)}")
            return False

    def test_flow1_submission_with_excel(self, file_data: Dict[str, Any]) -> Optional[str]:
        """测试flow1工作流提交（包含Excel文件）"""
        try:
            print(f"📤 Submitting flow1 with Excel file: {file_data['filename']}")
            
            # 方法1: 尝试使用multipart/form-data格式提交
            files = {
                'shopfile': (
                    file_data['filename'],
                    base64.b64decode(file_data['content']),
                    file_data['content_type']
                )
            }
            
            # 添加其他表单数据
            form_data = {
                'user_name': 'test_user',
                'processing_mode': 'excel_analysis',
                'notification': 'true'
            }
            
            # 提交到flow1的API端点 - 使用正确的flow_id和版本
            response = self.session.post(
                f"{self.base_url}/api/flows/abba-ccdd-eeff-1.0.0/submit",
                files=files,
                data=form_data,
                allow_redirects=False
            )
            
            if response.status_code == 302:  # 重定向成功
                redirect_url = response.headers.get('location', '')
                self.log_test("Flow1 Excel Submission", True,
                             f"Submitted successfully, redirecting to: {redirect_url}")
                
                # 提取thread_id
                if 'thread_id=' in redirect_url:
                    thread_id = redirect_url.split('thread_id=')[1].split('&')[0]
                    print(f"    ✅ Extracted thread_id: {thread_id}")
                    return thread_id
                else:
                    return "redirect_success"
                    
            elif response.status_code == 200:
                # 可能返回JSON响应
                try:
                    result = response.json()
                    thread_id = result.get("thread_id")
                    if thread_id:
                        self.log_test("Flow1 Excel Submission", True,
                                     f"Submitted successfully, thread_id: {thread_id}")
                        return thread_id
                except json.JSONDecodeError:
                    pass
            
            # 如果上述方法失败，尝试方法2: 直接发送JSON数据
            print("    🔄 Trying alternative submission method...")
            return self.test_flow1_submission_json_method(file_data, form_data)
            
        except Exception as e:
            self.log_test("Flow1 Excel Submission", False, f"Error: {str(e)}")
            return None

    def test_flow1_submission_json_method(self, file_data: Dict[str, Any], 
                                         additional_data: Dict[str, Any]) -> Optional[str]:
        """使用JSON方法提交flow1工作流"""
        try:
            # 准备JSON格式的提交数据
            submission_data = {
                "input_data": {
                    "shopfile": file_data,  # 包含完整的文件信息
                    **additional_data
                }
            }
            
            response = self.session.post(
                f"{self.base_url}/api/flows/abba-ccdd-eeff/start/version/1.0.0",
                json=submission_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                result = response.json()
                thread_id = result.get("thread_id")
                if thread_id:
                    self.log_test("Flow1 JSON Submission", True,
                                 f"Alternative method successful, thread_id: {thread_id}")
                    return thread_id
                else:
                    self.log_test("Flow1 JSON Submission", False,
                                 f"No thread_id in response: {result}")
                    return None
            else:
                self.log_test("Flow1 JSON Submission", False,
                             f"HTTP {response.status_code}: {response.text[:200]}")
                return None
                
        except Exception as e:
            self.log_test("Flow1 JSON Submission", False, f"Error: {str(e)}")
            return None

    def monitor_workflow_execution(self, thread_id: str, timeout: int = 60) -> bool:
        """监控工作流执行过程"""
        try:
            print(f"🔍 Monitoring workflow execution: {thread_id}")
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                # 获取工作流状态
                response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
                
                if response.status_code == 200:
                    status_data = response.json()
                    status = status_data.get("status", "unknown")
                    
                    print(f"    Status: {status}")
                    
                    if status in ["completed", "failed", "cancelled"]:
                        success = status == "completed"
                        self.log_test("Workflow Execution Monitoring", success,
                                     f"Final status: {status}")
                        return success
                    
                    # 等待一段时间再检查
                    time.sleep(2)
                else:
                    print(f"    Failed to get status: HTTP {response.status_code}")
                    time.sleep(2)
            
            # 超时
            self.log_test("Workflow Execution Monitoring", False,
                         f"Timeout after {timeout} seconds")
            return False
            
        except Exception as e:
            self.log_test("Workflow Execution Monitoring", False, f"Error: {str(e)}")
            return False

    def get_workflow_logs(self, thread_id: str) -> bool:
        """获取工作流执行日志"""
        try:
            print(f"📋 Retrieving workflow logs: {thread_id}")
            
            # 尝试获取日志
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}/logs")
            
            if response.status_code == 200:
                logs = response.json()
                log_count = len(logs) if isinstance(logs, list) else 0
                
                self.log_test("Workflow Logs Retrieval", True,
                             f"Retrieved {log_count} log entries")
                
                # 显示部分日志内容
                if isinstance(logs, list) and logs:
                    print("    📝 Sample log entries:")
                    for i, log_entry in enumerate(logs[:3]):  # 显示前3条
                        if isinstance(log_entry, dict):
                            message = log_entry.get('message', str(log_entry))
                            print(f"      {i+1}. {message}")
                        else:
                            print(f"      {i+1}. {log_entry}")
                
                return True
            else:
                self.log_test("Workflow Logs Retrieval", False,
                             f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Workflow Logs Retrieval", False, f"Error: {str(e)}")
            return False

    def test_console_access(self, thread_id: str) -> bool:
        """测试控制台页面访问"""
        try:
            console_url = f"{self.base_url}/sample_app/flow1?tab=logs&thread_id={thread_id}"
            print(f"🖥️  Accessing console: {console_url}")
            
            response = self.session.get(console_url)
            
            if response.status_code == 200:
                content = response.text
                
                # 检查关键元素
                key_elements = [
                    "flow1",
                    "thread_id",
                    "好店推荐10.xlsx",  # 检查是否显示了Excel文件名
                    "循环",  # flow1的循环功能
                ]
                
                found_elements = []
                for element in key_elements:
                    if element in content:
                        found_elements.append(element)
                
                success = len(found_elements) >= 2
                self.log_test("Console Access", success,
                             f"Found elements: {found_elements}")
                return success
            else:
                self.log_test("Console Access", False,
                             f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Console Access", False, f"Error: {str(e)}")
            return False

    def run_complete_test(self):
        """运行完整的flow1 Excel提交测试"""
        print("🚀 Starting Flow1 Excel Submission Test")
        print("=" * 60)
        print(f"📁 Excel File: {self.excel_file_path}")
        print(f"🌐 Server URL: {self.base_url}")
        print("=" * 60)

        # 1. 检查Excel文件
        print("\n📋 Step 1: Check Excel File")
        print("-" * 30)
        if not self.check_excel_file():
            print("❌ Cannot continue - Excel file not found")
            self.print_summary()
            return

        # 2. 准备文件数据
        print("\n🔧 Step 2: Prepare File Data")
        print("-" * 30)
        file_data = self.prepare_excel_file_data()
        if not file_data:
            print("❌ Cannot continue - file preparation failed")
            self.print_summary()
            return

        # 3. 测试服务器健康状态
        print("\n🏥 Step 3: Server Health Check")
        print("-" * 30)
        if not self.test_server_health():
            print("❌ Cannot continue - server not accessible")
            self.print_summary()
            return

        # 4. 提交flow1工作流
        print("\n📤 Step 4: Submit Flow1 with Excel")
        print("-" * 30)
        thread_id = self.test_flow1_submission_with_excel(file_data)
        if not thread_id:
            print("❌ Cannot continue - workflow submission failed")
            self.print_summary()
            return

        # 5. 监控工作流执行
        print("\n🔍 Step 5: Monitor Workflow Execution")
        print("-" * 30)
        execution_success = self.monitor_workflow_execution(thread_id, timeout=90)

        # 6. 获取工作流日志
        print("\n📋 Step 6: Retrieve Workflow Logs")
        print("-" * 30)
        logs_success = self.get_workflow_logs(thread_id)

        # 7. 测试控制台访问
        print("\n🖥️  Step 7: Test Console Access")
        print("-" * 30)
        console_success = self.test_console_access(thread_id)

        # 打印总结
        self.print_summary()

        # 特别说明
        print("\n" + "=" * 60)
        print("📊 Flow1 Excel Processing Analysis")
        print("=" * 60)
        print("Flow1 is designed to:")
        print("  1. 📁 Read Excel files from form submissions")
        print("  2. 🔄 Process Excel data row by row in a loop")
        print("  3. ⏱️  Display processing progress with timestamps")
        print("  4. 📝 Log detailed information about Excel content")
        print("  5. ⏸️  Support pause/resume functionality")
        print()
        print("Expected behavior with '好店推荐10.xlsx':")
        print("  - File will be detected as Excel format")
        print("  - Content will be read using pandas")
        print("  - Each row will be processed in the loop")
        print("  - Processing details will appear in logs")

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Test Summary")
        print("=" * 60)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed / total * 100:.1f}%" if total > 0 else "No tests run")

        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🎯 Key Test Results:")
        key_tests = [
            "Excel File Check",
            "Excel File Preparation", 
            "Server Health Check",
            "Flow1 Excel Submission",
            "Workflow Execution Monitoring",
            "Workflow Logs Retrieval",
            "Console Access"
        ]

        for test_name in key_tests:
            result = next((r for r in self.test_results if r["test"] == test_name), None)
            if result:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {test_name}")

        overall_success = passed == total and total > 0
        print(f"\n🏆 Overall Result: {'SUCCESS' if overall_success else 'PARTIAL SUCCESS' if passed > 0 else 'FAILED'}")

def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Flow1 Excel Submission Test")
    parser.add_argument("--url", default="http://localhost:8889",
                        help="Server base URL (default: http://localhost:8889)")
    parser.add_argument("--file", 
                        default="/Users/haowu/IdeaProjects/ai-product-selector3/docs/好店推荐10.xlsx",
                        help="Excel file path")

    args = parser.parse_args()

    tester = Flow1ExcelTest(args.url)
    if args.file != tester.excel_file_path:
        tester.excel_file_path = args.file
        print(f"📁 Using custom Excel file: {args.file}")

    tester.run_complete_test()

if __name__ == "__main__":
    main()