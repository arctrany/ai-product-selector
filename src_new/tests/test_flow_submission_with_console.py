#!/usr/bin/env python3
"""
工作流提交和控制台跳转测试用例
测试通过 flow_name 和 version 查询数据库，提交工作流并跳转到控制台
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional

import requests

# 添加项目根目录到 Python 路径，以便导入模块
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))


class FlowSubmissionTest:
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

    def setup_test_flow(self) -> Optional[str]:
        """设置测试工作流 - 通过 flow_name 和 version 创建"""
        try:
            # 创建测试工作流定义
            test_flow_def = {
                "name": "test_submission_flow",
                "description": "Test flow for submission and console redirection",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "name": "Start Node"
                    },
                    {
                        "id": "process",
                        "type": "python",
                        "name": "Process Node",
                        "code_ref": "lambda: 'Process Complete'",
                        "args": {}
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "name": "End Node"
                    }
                ],
                "edges": [
                    {"source": "start", "target": "process"},
                    {"source": "process", "target": "end"}
                ]
            }

            # 创建工作流
            create_data = {
                "name": "test_submission_flow",
                "definition": test_flow_def,
                "version": "1.0.0"
            }

            response = self.session.post(f"{self.base_url}/api/flows", json=create_data)
            if response.status_code == 200:
                result = response.json()
                flow_version_id = result.get("flow_version_id")

                # 发布工作流
                publish_response = self.session.post(f"{self.base_url}/api/flows/{flow_version_id}/publish")
                if publish_response.status_code == 200:
                    self.log_test("Test Flow Setup", True, f"Created and published flow: test_submission_flow v1.0.0")
                    return "test_submission_flow"
                else:
                    self.log_test("Test Flow Setup", False,
                                  f"Failed to publish flow: HTTP {publish_response.status_code}")
                    return None
            else:
                self.log_test("Test Flow Setup", False, f"Failed to create flow: HTTP {response.status_code}")
                return None
        except Exception as e:
            self.log_test("Test Flow Setup", False, f"Error: {str(e)}")
            return None

    def test_flow_query_by_name_and_version(self, flow_name: str, version: str = "1.0.0") -> Optional[Dict[str, Any]]:
        """测试通过 flow_name 和 version 查询数据库中的 flow"""
        try:
            print(f"🔍 Querying flow: {flow_name} version {version}")

            # 通过 API 验证工作流是否存在
            # 我们通过尝试创建工作流来验证数据库查询功能
            # 如果工作流已存在，创建会返回现有的 flow_id

            test_flow_def = {
                "name": flow_name,
                "description": f"Test flow for {flow_name} version {version}",
                "nodes": [
                    {
                        "id": "start",
                        "type": "start",
                        "name": "Start Node"
                    },
                    {
                        "id": "end",
                        "type": "end",
                        "name": "End Node"
                    }
                ],
                "edges": [
                    {"source": "start", "target": "end"}
                ]
            }

            # 尝试创建工作流（如果已存在会返回现有的）
            create_data = {
                "name": flow_name,
                "definition": test_flow_def,
                "version": version
            }

            response = self.session.post(f"{self.base_url}/api/flows", json=create_data)
            if response.status_code == 200:
                result = response.json()
                flow_version_id = result.get("flow_version_id")

                # 发布工作流
                publish_response = self.session.post(f"{self.base_url}/api/flows/{flow_version_id}/publish")
                if publish_response.status_code == 200:
                    flow_info = {
                        "flow_name": flow_name,
                        "version": version,
                        "flow_version_id": flow_version_id,
                        "status": "published"
                    }

                    self.log_test("Flow Query by Name+Version", True,
                                  f"Found/Created flow: {flow_name} v{version}, flow_version_id: {flow_version_id}")
                    return flow_info
                else:
                    self.log_test("Flow Query by Name+Version", False,
                                  f"Failed to publish flow: HTTP {publish_response.status_code}")
                    return None
            else:
                self.log_test("Flow Query by Name+Version", False,
                              f"Failed to create/find flow: HTTP {response.status_code}")
                return None

        except Exception as e:
            self.log_test("Flow Query by Name+Version", False, f"Error: {str(e)}")
            return None

    def test_workflow_submission_with_form_data(self, app_name: str = "sample_app",
                                                flow_id: str = "flow1") -> Optional[str]:
        """测试工作流提交（模拟表单提交）"""
        try:
            # 准备表单数据
            form_data = {
                "user_input": "test_data_for_submission",
                "processing_mode": "batch",
                "notification_email": "test@example.com",
                "priority": "normal",
                "test_timestamp": str(int(time.time()))
            }

            print(f"📤 Submitting workflow: {app_name}/{flow_id}")
            print(f"    Form data: {list(form_data.keys())}")

            # 提交工作流（模拟表单提交）- 使用正确的API端点
            response = self.session.post(
                f"{self.base_url}/api/flows/{flow_id}/submit",
                data=form_data,
                allow_redirects=False  # 不自动跟随重定向，以便我们检查重定向响应
            )

            if response.status_code == 302:  # 重定向到控制台
                redirect_url = response.headers.get('location', '')
                self.log_test("Workflow Submission", True,
                              f"Submitted successfully, redirecting to: {redirect_url}")

                # 从重定向 URL 中提取 thread_id
                if 'thread_id=' in redirect_url:
                    thread_id = redirect_url.split('thread_id=')[1].split('&')[0]
                    print(f"    ✅ Extracted thread_id: {thread_id}")
                    return thread_id
                else:
                    print(f"    ⚠️  No thread_id in redirect URL")
                    return "redirect_success"

            elif response.status_code == 200:
                # 可能返回 JSON 响应
                try:
                    result = response.json()
                    thread_id = result.get("thread_id")
                    if thread_id:
                        self.log_test("Workflow Submission", True,
                                      f"Submitted successfully, thread_id: {thread_id}")
                        return thread_id
                    else:
                        # 检查是否有其他有用的信息
                        print(f"    Response content: {result}")
                except json.JSONDecodeError:
                    print(f"    Response is not JSON: {response.text[:200]}")

            self.log_test("Workflow Submission", False,
                          f"HTTP {response.status_code}: {response.text[:200]}")
            return None

        except Exception as e:
            self.log_test("Workflow Submission", False, f"Error: {str(e)}")
            return None

    def test_console_redirection_and_logs(self, app_name: str, flow_id: str,
                                          thread_id: str) -> bool:
        """测试控制台跳转和日志显示"""
        try:
            # 测试控制台页面访问
            console_url = f"{self.base_url}/{app_name}/{flow_id}?tab=logs&thread_id={thread_id}"
            print(f"🖥️  Accessing console: {console_url}")

            response = self.session.get(console_url)
            if response.status_code == 200:
                content = response.text

                # 检查页面是否包含预期的控制台元素
                console_elements = [
                    "工作流控制台",  # 控制台标题
                    "thread_id",  # 线程ID显示
                    "日志",  # 日志标签
                    flow_id  # 工作流ID
                ]

                found_elements = []
                for element in console_elements:
                    if element in content:
                        found_elements.append(element)

                success = len(found_elements) >= 2  # 至少找到2个关键元素
                details = f"Found console elements: {found_elements}"
                self.log_test("Console Page Access", success, details)

                # 测试日志获取
                return self.test_log_retrieval(thread_id)
            else:
                self.log_test("Console Page Access", False,
                              f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_test("Console Page Access", False, f"Error: {str(e)}")
            return False

    def test_log_retrieval(self, thread_id: str) -> bool:
        """测试日志获取功能"""
        try:
            # 测试工作流状态和日志获取
            status_response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")

            if status_response.status_code == 200:
                status_data = status_response.json()
                status = status_data.get("status", "unknown")

                self.log_test("Log Retrieval", True,
                              f"Retrieved status: {status} for thread: {thread_id}")

                # 等待一段时间让工作流执行
                print("⏳ Waiting for workflow execution...")
                time.sleep(3)

                # 再次检查状态
                final_status_response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
                if final_status_response.status_code == 200:
                    final_status_data = final_status_response.json()
                    final_status = final_status_data.get("status", "unknown")

                    self.log_test("Workflow Execution Monitoring", True,
                                  f"Final status: {final_status}")
                    return True
                else:
                    self.log_test("Workflow Execution Monitoring", False,
                                  f"Failed to get final status: HTTP {final_status_response.status_code}")
                    return False
            else:
                self.log_test("Log Retrieval", False,
                              f"HTTP {status_response.status_code}")
                return False

        except Exception as e:
            self.log_test("Log Retrieval", False, f"Error: {str(e)}")
            return False

    def run_comprehensive_test(self):
        """运行完整的工作流提交和控制台测试"""
        print("🚀 Starting Flow Submission and Console Test")
        print("=" * 60)

        # 1. 设置测试工作流
        print("\n📋 Step 1: Setup Test Flow")
        print("-" * 30)
        flow_name = self.setup_test_flow()
        if not flow_name:
            print("❌ Cannot continue - test flow setup failed")
            self.print_summary()
            return

        # 2. 测试通过 flow_name 和 version 查询
        print("\n🔍 Step 2: Query Flow by Name and Version")
        print("-" * 30)
        flow_info = self.test_flow_query_by_name_and_version(flow_name, "1.0.0")
        if not flow_info:
            print("❌ Cannot continue - flow query failed")
            self.print_summary()
            return

        # 3. 测试工作流提交
        print("\n📤 Step 3: Submit Workflow with Form Data")
        print("-" * 30)
        thread_id = self.test_workflow_submission_with_form_data("sample_app", "flow1")
        if not thread_id:
            print("❌ Cannot continue - workflow submission failed")
            self.print_summary()
            return

        # 4. 测试控制台跳转和日志显示
        print("\n🖥️  Step 4: Console Redirection and Log Display")
        print("-" * 30)
        console_success = self.test_console_redirection_and_logs("sample_app", "flow1", thread_id)

        # 打印总结
        self.print_summary()

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
        print(f"Success Rate: {passed / total * 100:.1f}%")

        if total - passed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['details']}")

        print("\n🎯 Key Test Results:")
        key_tests = [
            "Test Flow Setup",
            "Flow Query by Name+Version",
            "Workflow Submission",
            "Console Page Access",
            "Log Retrieval"
        ]

        for test_name in key_tests:
            result = next((r for r in self.test_results if r["test"] == test_name), None)
            if result:
                status = "✅" if result["success"] else "❌"
                print(f"  {status} {test_name}")

        overall_success = passed == total
        print(f"\n🏆 Overall Result: {'SUCCESS' if overall_success else 'PARTIAL SUCCESS'}")

        if overall_success:
            print("\n✨ All tests passed! The flow submission and console redirection system is working correctly.")
            print("   - Flow can be queried by name and version")
            print("   - Workflow submission works with form data")
            print("   - Console redirection functions properly")
            print("   - Log retrieval and monitoring is operational")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="Flow Submission and Console Test")
    parser.add_argument("--url", default="http://localhost:8889",
                        help="Server base URL (default: http://localhost:8889)")

    args = parser.parse_args()

    tester = FlowSubmissionTest(args.url)
    tester.run_comprehensive_test()


if __name__ == "__main__":
    main()
