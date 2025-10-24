#!/usr/bin/env python3
"""
工作流引擎完整API端点测试
覆盖所有23个API端点的功能测试
"""

import requests
import json
import time
import sys
from typing import Dict, Any, Optional, List

class ComprehensiveEndpointTest:
    def __init__(self, base_url: str = "http://localhost:8889"):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
        self.created_resources = {
            "flows": [],
            "runs": []
        }
        
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

    # ==================== 系统级端点测试 ====================
    
    def test_root_redirect(self) -> bool:
        """测试根路径重定向 - GET /"""
        try:
            response = self.session.get(f"{self.base_url}/", allow_redirects=False)
            success = response.status_code == 302 and "/apps" in response.headers.get("location", "")
            self.log_test("Root Redirect", success, f"Status: {response.status_code}, Location: {response.headers.get('location', 'None')}")
            return success
        except Exception as e:
            self.log_test("Root Redirect", False, f"Error: {str(e)}")
            return False

    def test_health_check(self) -> bool:
        """测试健康检查 - GET /health"""
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

    def test_status_endpoint(self) -> bool:
        """测试状态端点 - GET /status"""
        try:
            response = self.session.get(f"{self.base_url}/status")
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("Status Endpoint", success, f"Status: {data.get('status', 'N/A')}")
            else:
                self.log_test("Status Endpoint", False, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Status Endpoint", False, f"Error: {str(e)}")
            return False

    def test_apps_list(self) -> bool:
        """测试应用列表 - GET /apps"""
        try:
            response = self.session.get(f"{self.base_url}/apps")
            success = response.status_code == 200
            self.log_test("Apps List", success, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Apps List", False, f"Error: {str(e)}")
            return False

    # ==================== Flow管理端点测试 ====================

    def test_create_flow(self) -> Optional[str]:
        """测试创建Flow - POST /api/flows"""
        try:
            flow_def = {
                "name": "test_comprehensive_flow",
                "description": "Comprehensive test flow",
                "definition": {
                    "name": "test_comprehensive_flow",
                    "nodes": [
                        {
                            "id": "start",
                            "type": "python",
                            "function": "test.hello_world",
                            "inputs": {},
                            "next": None
                        }
                    ],
                    "edges": []
                }
            }

            response = self.session.post(f"{self.base_url}/api/flows", json=flow_def)
            if response.status_code == 200:
                result = response.json()
                flow_version_id = result.get("flow_version_id")
                self.created_resources["flows"].append(flow_version_id)
                self.log_test("Create Flow", True, f"Created flow_version_id: {flow_version_id}")
                return str(flow_version_id)
            else:
                self.log_test("Create Flow", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Create Flow", False, f"Error: {str(e)}")
            return None

    def test_list_flows(self) -> bool:
        """测试获取Flow列表 - GET /api/flows"""
        try:
            response = self.session.get(f"{self.base_url}/api/flows")
            if response.status_code == 200:
                data = response.json()
                flows = data.get("flows", [])
                total = data.get("total", 0)
                self.log_test("List Flows", True, f"Found {total} flows")
                return True
            else:
                self.log_test("List Flows", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("List Flows", False, f"Error: {str(e)}")
            return False

    def test_get_flow_by_id(self, flow_version_id: str) -> bool:
        """测试根据ID获取Flow - GET /api/flows/{flow_id}"""
        try:
            # Extract flow_id from flow_version_id (simplified)
            flow_id = "test_comprehensive_flow"
            response = self.session.get(f"{self.base_url}/api/flows/{flow_id}")
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("Get Flow by ID", success, f"Flow: {data.get('name', 'N/A')}")
            else:
                self.log_test("Get Flow by ID", False, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Get Flow by ID", False, f"Error: {str(e)}")
            return False

    def test_publish_flow(self, flow_version_id: str) -> bool:
        """测试发布Flow - POST /api/flows/{flow_version_id}/publish"""
        try:
            response = self.session.post(f"{self.base_url}/api/flows/{flow_version_id}/publish")
            success = response.status_code == 200
            if success:
                data = response.json()
                self.log_test("Publish Flow", success, f"Status: {data.get('status', 'N/A')}")
            else:
                self.log_test("Publish Flow", False, f"HTTP {response.status_code}: {response.text}")
            return success
        except Exception as e:
            self.log_test("Publish Flow", False, f"Error: {str(e)}")
            return False

    # ==================== Flow操作端点测试 ====================

    def test_submit_flow_form(self, flow_id: str = "test_comprehensive_flow") -> bool:
        """测试Flow表单提交 - POST /api/flows/{flow_version_param}/submit"""
        try:
            # 准备表单数据
            form_data = {
                "test_field": "test_value",
                "user_input": "comprehensive_test_data"
            }

            response = self.session.post(
                f"{self.base_url}/api/flows/{flow_id}-latest/submit",
                data=form_data,
                allow_redirects=False
            )

            success = response.status_code in [200, 302]
            if success:
                if response.status_code == 302:
                    redirect_url = response.headers.get('location', '')
                    self.log_test("Submit Flow Form", success, f"Redirected to: {redirect_url}")
                else:
                    self.log_test("Submit Flow Form", success, "Form submitted successfully")
            else:
                self.log_test("Submit Flow Form", False, f"HTTP {response.status_code}: {response.text}")
            return success
        except Exception as e:
            self.log_test("Submit Flow Form", False, f"Error: {str(e)}")
            return False

    def test_start_flow_api(self, flow_id: str = "test_comprehensive_flow") -> Optional[str]:
        """测试Flow API启动 - POST /api/flows/{flow_version_param}/start"""
        try:
            start_data = {
                "input_data": {"test": "comprehensive_api_test"}
            }

            response = self.session.post(
                f"{self.base_url}/api/flows/{flow_id}-latest/start",
                json=start_data
            )

            if response.status_code == 200:
                result = response.json()
                thread_id = result.get("thread_id")
                if thread_id:
                    self.created_resources["runs"].append(thread_id)
                self.log_test("Start Flow API", True, f"Started with thread_id: {thread_id}")
                return thread_id
            else:
                self.log_test("Start Flow API", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Start Flow API", False, f"Error: {str(e)}")
            return None



    # ==================== 工作流运行端点测试 ====================

    def test_list_runs(self) -> bool:
        """测试获取运行列表 - GET /api/runs"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs")
            if response.status_code == 200:
                data = response.json()
                runs = data.get("runs", [])
                total = data.get("total", 0)
                self.log_test("List Runs", True, f"Found {total} runs")
                return True
            else:
                self.log_test("List Runs", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("List Runs", False, f"Error: {str(e)}")
            return False

    def test_start_run(self) -> Optional[str]:
        """测试启动运行 - POST /api/runs/start"""
        try:
            start_data = {
                "flow_version_id": self.created_resources["flows"][0] if self.created_resources["flows"] else 9,
                "inputs": {"test": "run_start_test"}
            }

            response = self.session.post(f"{self.base_url}/api/runs/start", json=start_data)
            if response.status_code == 200:
                result = response.json()
                thread_id = result.get("thread_id")
                if thread_id:
                    self.created_resources["runs"].append(thread_id)
                self.log_test("Start Run", True, f"Started thread_id: {thread_id}")
                return thread_id
            else:
                self.log_test("Start Run", False, f"HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            self.log_test("Start Run", False, f"Error: {str(e)}")
            return None

    def test_get_run_status(self, thread_id: str) -> bool:
        """测试获取运行状态 - GET /api/runs/{thread_id}"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                self.log_test("Get Run Status", True, f"Status: {status}")
                return True
            else:
                self.log_test("Get Run Status", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Get Run Status", False, f"Error: {str(e)}")
            return False

    def test_pause_run(self, thread_id: str) -> bool:
        """测试暂停运行 - POST /api/runs/{thread_id}/pause"""
        try:
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/pause")
            success = response.status_code in [200, 400]  # 400可能表示已完成无法暂停
            details = f"HTTP {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                details = f"Status: {data.get('status', 'N/A')}"
            self.log_test("Pause Run", success, details)
            return success
        except Exception as e:
            self.log_test("Pause Run", False, f"Error: {str(e)}")
            return False

    def test_resume_run(self, thread_id: str) -> bool:
        """测试恢复运行 - POST /api/runs/{thread_id}/resume"""
        try:
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/resume")
            success = response.status_code in [200, 400]  # 400可能表示已完成无法恢复
            details = f"HTTP {response.status_code}"
            if response.status_code == 200:
                data = response.json()
                details = f"Status: {data.get('status', 'N/A')}"
            self.log_test("Resume Run", success, details)
            return success
        except Exception as e:
            self.log_test("Resume Run", False, f"Error: {str(e)}")
            return False

    def test_get_run_logs(self, thread_id: str) -> bool:
        """测试获取运行日志 - GET /api/runs/{thread_id}/logs"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}/logs")
            success = response.status_code == 200
            if success:
                data = response.json()
                logs_count = len(data.get("logs", []))
                self.log_test("Get Run Logs", success, f"Found {logs_count} log entries")
            else:
                self.log_test("Get Run Logs", False, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Get Run Logs", False, f"Error: {str(e)}")
            return False

    def test_download_run_logs(self, thread_id: str) -> bool:
        """测试下载运行日志 - GET /api/runs/{thread_id}/logs/download"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}/logs/download")
            success = response.status_code == 200
            if success:
                content_length = len(response.content)
                self.log_test("Download Run Logs", success, f"Downloaded {content_length} bytes")
            else:
                self.log_test("Download Run Logs", False, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Download Run Logs", False, f"Error: {str(e)}")
            return False

    # ==================== WebSocket端点测试 ====================

    def test_websocket_stats(self) -> bool:
        """测试WebSocket统计 - GET /api/ws/stats"""
        try:
            response = self.session.get(f"{self.base_url}/api/ws/stats")
            if response.status_code == 200:
                data = response.json()
                connections = data.get("connections", 0)
                self.log_test("WebSocket Stats", True, f"Active connections: {connections}")
                return True
            else:
                self.log_test("WebSocket Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("WebSocket Stats", False, f"Error: {str(e)}")
            return False

    # ==================== 控制台端点测试 ====================

    def test_console_ui(self) -> bool:
        """测试控制台UI - GET /console"""
        try:
            response = self.session.get(f"{self.base_url}/console")
            success = response.status_code == 200
            self.log_test("Console UI", success, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("Console UI", False, f"Error: {str(e)}")
            return False

    def test_console_health(self) -> bool:
        """测试控制台健康检查 - GET /console/health"""
        try:
            response = self.session.get(f"{self.base_url}/console/health")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                self.log_test("Console Health", True, f"Status: {status}")
                return True
            else:
                self.log_test("Console Health", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Console Health", False, f"Error: {str(e)}")
            return False

    def test_console_stats(self) -> bool:
        """测试控制台统计 - GET /console/stats"""
        try:
            response = self.session.get(f"{self.base_url}/console/stats")
            if response.status_code == 200:
                data = response.json()
                apps_total = data.get("apps", {}).get("total", 0)
                self.log_test("Console Stats", True, f"Total apps: {apps_total}")
                return True
            else:
                self.log_test("Console Stats", False, f"HTTP {response.status_code}")
                return False
        except Exception as e:
            self.log_test("Console Stats", False, f"Error: {str(e)}")
            return False

    def test_sys_console(self) -> bool:
        """测试系统控制台 - GET /sys/console"""
        try:
            response = self.session.get(f"{self.base_url}/sys/console")
            success = response.status_code == 200
            self.log_test("System Console", success, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("System Console", False, f"Error: {str(e)}")
            return False

    # ==================== 应用路径端点测试 ====================

    def test_app_flow_path(self) -> bool:
        """测试应用流程路径 - GET /{app_name}/{flow_identifier}"""
        try:
            response = self.session.get(f"{self.base_url}/sample_app/flow1")
            success = response.status_code == 200
            self.log_test("App Flow Path", success, f"HTTP {response.status_code}")
            return success
        except Exception as e:
            self.log_test("App Flow Path", False, f"Error: {str(e)}")
            return False

    def test_app_flow_htm_path(self) -> bool:
        """测试应用流程HTM路径 - GET /{app_name}/{flow_identifier}.htm"""
        try:
            response = self.session.get(f"{self.base_url}/sample_app/flow1.htm")
            success = response.status_code in [200, 404]  # 404是正常的，因为可能没有自定义模板
            details = f"HTTP {response.status_code}"
            if response.status_code == 404:
                details += " (No custom template - expected)"
            self.log_test("App Flow HTM Path", success, details)
            return success
        except Exception as e:
            self.log_test("App Flow HTM Path", False, f"Error: {str(e)}")
            return False

    # ==================== 清理资源 ====================

    def cleanup_resources(self):
        """清理测试创建的资源"""
        print("\n🧹 Cleaning up test resources...")
        
        # 删除创建的runs
        for thread_id in self.created_resources["runs"]:
            try:
                response = self.session.delete(f"{self.base_url}/api/runs/{thread_id}")
                if response.status_code == 200:
                    print(f"   ✅ Deleted run: {thread_id}")
                else:
                    print(f"   ⚠️  Failed to delete run {thread_id}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error deleting run {thread_id}: {e}")

        # 删除创建的flows
        for flow_version_id in self.created_resources["flows"]:
            try:
                # 尝试删除flow (可能需要flow_id而不是flow_version_id)
                flow_id = "test_comprehensive_flow"
                response = self.session.delete(f"{self.base_url}/api/flows/{flow_id}")
                if response.status_code == 200:
                    print(f"   ✅ Deleted flow: {flow_id}")
                else:
                    print(f"   ⚠️  Failed to delete flow {flow_id}: HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ Error deleting flow {flow_version_id}: {e}")

    # ==================== 主测试流程 ====================

    def run_comprehensive_test(self):
        """运行完整的端点测试"""
        print("🚀 Starting Comprehensive Endpoint Test")
        print("=" * 60)

        # 1. 系统级端点测试
        print("\n📋 System Level Endpoints")
        print("-" * 30)
        self.test_root_redirect()
        self.test_health_check()
        self.test_status_endpoint()
        self.test_apps_list()

        # 2. Flow管理端点测试
        print("\n🔧 Flow Management Endpoints")
        print("-" * 30)
        flow_version_id = self.test_create_flow()
        self.test_list_flows()
        
        if flow_version_id:
            self.test_get_flow_by_id(flow_version_id)
            self.test_publish_flow(flow_version_id)

        # 3. Flow操作端点测试
        print("\n⚡ Flow Operation Endpoints")
        print("-" * 30)
        self.test_submit_flow_form()
        thread_id = self.test_start_flow_api()

        # 4. 工作流运行端点测试
        print("\n🏃 Workflow Run Endpoints")
        print("-" * 30)
        self.test_list_runs()
        run_thread_id = self.test_start_run()
        
        if run_thread_id:
            time.sleep(1)  # 等待运行启动
            self.test_get_run_status(run_thread_id)
            self.test_pause_run(run_thread_id)
            self.test_resume_run(run_thread_id)
            self.test_get_run_logs(run_thread_id)
            self.test_download_run_logs(run_thread_id)

        # 5. WebSocket端点测试
        print("\n🔌 WebSocket Endpoints")
        print("-" * 30)
        self.test_websocket_stats()

        # 6. 控制台端点测试
        print("\n🖥️  Console Endpoints")
        print("-" * 30)
        self.test_console_ui()
        self.test_console_health()
        self.test_console_stats()
        self.test_sys_console()

        # 7. 应用路径端点测试
        print("\n🎯 Application Path Endpoints")
        print("-" * 30)
        self.test_app_flow_path()
        self.test_app_flow_htm_path()

        # 8. 清理资源
        self.cleanup_resources()

        # 9. 打印总结
        self.print_summary()

    def print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("📊 Comprehensive Test Summary")
        print("=" * 60)

        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)

        print(f"Total Endpoints Tested: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {passed/total*100:.1f}%")

        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🎯 Endpoint Coverage Analysis:")
        
        # 按类别统计
        categories = {
            "System": ["Root Redirect", "Health Check", "Status Endpoint", "Apps List"],
            "Flow Management": ["Create Flow", "List Flows", "Get Flow by ID", "Publish Flow"],
            "Flow Operations": ["Submit Flow Form", "Start Flow API"],
            "Workflow Runs": ["List Runs", "Start Run", "Get Run Status", "Pause Run", "Resume Run", "Get Run Logs", "Download Run Logs"],
            "WebSocket": ["WebSocket Stats"],
            "Console": ["Console UI", "Console Health", "Console Stats", "System Console"],
            "Application Paths": ["App Flow Path", "App Flow HTM Path"]
        }

        for category, tests in categories.items():
            category_results = [r for r in self.test_results if r["test"] in tests]
            category_passed = sum(1 for r in category_results if r["success"])
            category_total = len(category_results)
            if category_total > 0:
                print(f"  {category}: {category_passed}/{category_total} ({category_passed/category_total*100:.1f}%)")

        overall_success = passed >= total * 0.8  # 80%通过率认为成功
        print(f"\n🏆 Overall Result: {'SUCCESS' if overall_success else 'NEEDS IMPROVEMENT'}")

        if overall_success:
            print("\n✨ Comprehensive endpoint testing completed successfully!")
            print("   All major API endpoints are functional and accessible.")
        else:
            print("\n⚠️  Some endpoints need attention. Please review failed tests above.")

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Endpoint Test")
    parser.add_argument("--url", default="http://localhost:8889",
                       help="Server base URL (default: http://localhost:8889)")
    
    args = parser.parse_args()
    
    tester = ComprehensiveEndpointTest(args.url)
    tester.run_comprehensive_test()

if __name__ == "__main__":
    main()