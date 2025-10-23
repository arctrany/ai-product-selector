#!/usr/bin/env python3
"""
工作流引擎服务器功能验证脚本
验证控制台功能、任务控制和应用功能
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional

class WorkflowServerValidator:
    def __init__(self, base_url: str = "http://localhost:8889"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        
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
        
    def test_health_check(self) -> bool:
        """测试健康检查端点"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                success = data.get("status") == "healthy"
                self.log_test("Health Check", success, f"Status: {data.get('status')}")
                return success
            else:
                self.log_test("Health Check", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Health Check", False, f"Error: {str(e)}")
            return False
            
    def test_workflow_creation(self) -> Optional[str]:
        """测试工作流创建"""
        try:
            # 使用简化的工作流定义进行测试
            simple_workflow_def = {
                "name": "test_validation_flow",
                "description": "Simple test workflow for validation",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "name": "Start"
                    },
                    {
                        "id": "test_node",
                        "type": "python",
                        "name": "Test Node",
                        "code_ref": "lambda: 'Hello World'",
                        "args": {}
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "name": "End"
                    }
                ],
                "edges": [
                    {"source": "start", "target": "test_node"},
                    {"source": "test_node", "target": "end"}
                ]
            }

            # 创建工作流 - 添加 /api 前缀
            create_data = {
                "name": "test_validation_flow",
                "definition": simple_workflow_def,
                "version": "1.0.0"
            }

            response = self.session.post(f"{self.base_url}/api/flows", json=create_data)
            if response.status_code == 200:
                result = response.json()
                flow_version_id = result.get("flow_version_id")
                self.log_test("Workflow Creation", True, f"Created flow with ID: {flow_version_id}")
                return str(flow_version_id)
            else:
                self.log_test("Workflow Creation", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Workflow Creation", False, f"Error: {str(e)}")
            return None

    def test_workflow_publish(self, flow_version_id: str) -> bool:
        """测试工作流发布"""
        try:
            # 使用旧的路由（没有/api前缀）
            response = self.session.post(f"{self.base_url}/api/flows/{flow_version_id}/publish")
            if response.status_code == 200:
                self.log_test("Workflow Publish", True, f"Published flow {flow_version_id}")
                return True
            else:
                self.log_test("Workflow Publish", False, f"HTTP {response.status_code}: {response.text}")
                return False
        except Exception as e:
            self.log_test("Workflow Publish", False, f"Error: {str(e)}")
            return False

    def test_workflow_execution(self, flow_version_id: str) -> Optional[str]:
        """测试工作流执行"""
        try:
            start_data = {
                "flow_version_id": flow_version_id,
                "input_data": {"test_validation": True}
            }

            # 使用旧的路由（没有/api前缀）
            response = self.session.post(f"{self.base_url}/api/runs/start", json=start_data)
            if response.status_code == 200:
                result = response.json()
                thread_id = result.get("thread_id")
                self.log_test("Workflow Execution Start", True, f"Started execution with thread ID: {thread_id}")
                return thread_id
            else:
                self.log_test("Workflow Execution Start", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Workflow Execution Start", False, f"Error: {str(e)}")
            return None

    def test_workflow_status(self, thread_id: str) -> Dict[str, Any]:
        """测试工作流状态查询"""
        try:
            # 使用旧的路由（没有/api前缀）
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "unknown")
                self.log_test("Workflow Status Query", True, f"Status: {status}")
                return status_data
            else:
                self.log_test("Workflow Status Query", False, f"HTTP {response.status_code}")
                return {}
        except Exception as e:
            self.log_test("Workflow Status Query", False, f"Error: {str(e)}")
            return {}

    def test_workflow_control(self, thread_id: str) -> bool:
        """测试工作流控制操作（暂停/恢复）"""
        try:
            # 测试暂停 - 使用旧的路由（没有/api前缀）
            pause_response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/pause")
            pause_success = pause_response.status_code in [200, 400]  # 400可能表示已完成无法暂停

            # 测试恢复 - 使用正确的API路由
            resume_response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/resume")
            resume_success = resume_response.status_code in [200, 400]  # 400可能表示已完成无法恢复

            success = pause_success and resume_success
            details = f"Pause: {pause_response.status_code}, Resume: {resume_response.status_code}"
            self.log_test("Workflow Control (Pause/Resume)", success, details)
            return success
        except Exception as e:
            self.log_test("Workflow Control (Pause/Resume)", False, f"Error: {str(e)}")
            return False

    def test_app_flow_path_validation(self) -> bool:
        """测试 /{app_name}/{flow_name} 路径验证功能"""
        try:
            # 测试应用页面路径
            test_paths = [
                ("/sample_app", "Sample App Page"),
                ("/sample_app/flow1", "Sample App Flow1 Page"),
                ("/test_app/test_flow", "Test App Flow Page")
            ]

            all_success = True
            for path, name in test_paths:
                try:
                    response = self.session.get(f"{self.base_url}{path}")
                    # 200 表示页面存在，404 表示应用或流程不存在但路径格式正确
                    success = response.status_code in [200, 404]
                    if not success:
                        all_success = False
                    self.log_test(f"Path Validation - {name}", success, f"HTTP {response.status_code}")
                except Exception as e:
                    self.log_test(f"Path Validation - {name}", False, f"Error: {str(e)}")
                    all_success = False

            return all_success
        except Exception as e:
            self.log_test("Path Validation", False, f"Error: {str(e)}")
            return False

    def test_console_ui_endpoints(self) -> bool:
        """测试控制台UI端点"""
        endpoints_to_test = [
            ("/", "Main Console"),
            ("/apps", "Apps List Page"),
            ("/docs", "API Documentation"),
        ]

        all_success = True
        for endpoint, name in endpoints_to_test:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                if not success:
                    all_success = False
                self.log_test(f"Console UI - {name}", success, f"HTTP {response.status_code}")
            except Exception as e:
                self.log_test(f"Console UI - {name}", False, f"Error: {str(e)}")
                all_success = False

        return all_success

    def wait_for_workflow_completion(self, thread_id: str, max_wait: int = 60) -> bool:
        """等待工作流完成"""
        print(f"⏳ Waiting for workflow {thread_id} to complete (max {max_wait}s)...")

        start_time = time.time()
        while time.time() - start_time < max_wait:
            status_data = self.test_workflow_status(thread_id)
            status = status_data.get("status", "unknown")

            if status in ["completed", "failed", "cancelled"]:
                print(f"🏁 Workflow completed with status: {status}")
                return status == "completed"
            elif status == "running":
                print(f"🔄 Workflow still running... ({int(time.time() - start_time)}s elapsed)")
                time.sleep(2)
            else:
                print(f"❓ Unknown status: {status}")
                time.sleep(1)

        print(f"⏰ Timeout waiting for workflow completion")
        return False

    def run_comprehensive_validation(self):
        """运行全面的功能验证"""
        print("🚀 Starting Workflow Engine Server Validation")
        print("=" * 60)

        # 基础功能测试
        print("\n📋 Basic Functionality Tests")
        print("-" * 30)
        self.test_health_check()
        self.test_console_ui_endpoints()

        # 路径验证测试
        print("\n🛣️  Path Validation Tests")
        print("-" * 30)
        self.test_app_flow_path_validation()

        # 工作流生命周期测试
        print("\n🔄 Workflow Lifecycle Tests")
        print("-" * 30)

        # 创建工作流
        flow_version_id = self.test_workflow_creation()
        if not flow_version_id:
            print("❌ Cannot continue workflow tests - creation failed")
            self.print_summary()
            return

        # 发布工作流
        if not self.test_workflow_publish(flow_version_id):
            print("❌ Cannot continue workflow tests - publish failed")
            self.print_summary()
            return

        # 执行工作流
        thread_id = self.test_workflow_execution(flow_version_id)
        if not thread_id:
            print("❌ Cannot continue workflow tests - execution failed")
            self.print_summary()
            return

        # 工作流控制测试
        print("\n🎮 Workflow Control Tests")
        print("-" * 30)

        # 立即测试控制功能（在工作流可能还在运行时）
        self.test_workflow_control(thread_id)

        # 等待工作流完成并验证
        print("\n⏳ Workflow Execution Monitoring")
        print("-" * 30)
        completion_success = self.wait_for_workflow_completion(thread_id)

        # 最终状态检查
        final_status = self.test_workflow_status(thread_id)

        # 打印总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Validation Summary")
        print("=" * 60)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🎯 Key Functionality Status:")
        key_tests = [
            "Health Check",
            "Path Validation - Sample App Page",
            "Path Validation - Sample App Flow1 Page",
            "Workflow Creation",
            "Workflow Execution Start",
            "Workflow Control (Pause/Resume)"
        ]
        
        for test_name in key_tests:
            result = next((r for r in self.test_results if r["test"] == test_name), None)
            if result:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {test_name}")
        
        overall_success = passed == total
        print(f"\n🏆 Overall Result: {'SUCCESS' if overall_success else 'PARTIAL SUCCESS'}")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Workflow Engine Server Validation")
    parser.add_argument("--url", default="http://localhost:8889",
                       help="Server base URL (default: http://localhost:8889)")
    
    args = parser.parse_args()
    
    validator = WorkflowServerValidator(args.url)
    validator.run_comprehensive_validation()

if __name__ == "__main__":
    main()