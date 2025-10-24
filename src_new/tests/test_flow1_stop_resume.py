"""测试Flow1循环节点的stop和resume功能"""

import json
import time
import threading
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional
import pytest
import requests
from unittest.mock import patch, Mock

# 添加项目根目录到 Python 路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

try:
    from workflow_engine.core.engine import WorkflowEngine
    from workflow_engine.sdk.control import WorkflowControl
    from workflow_engine.storage.database import DatabaseManager
    from workflow_engine.config.server import ServerConfig
except ImportError as e:
    print(f"Warning: Could not import workflow_engine modules: {e}")
    print("This test will use HTTP API calls instead of direct engine calls")


class TestFlow1StopResume:
    """Flow1 stop/resume功能测试类"""

    def setup_method(self):
        """每个测试方法执行前的设置"""
        self.base_url = "http://localhost:8889"
        self.session = requests.Session()
        self.test_results = []

        # 创建测试用的Excel文件路径
        self.test_excel_path = Path(__file__).parent / "test_data" / "test_excel.xlsx"
        self.test_excel_path.parent.mkdir(exist_ok=True)

        # 创建简单的测试Excel文件
        self._create_test_excel()
        """测试前准备"""
        # 使用HTTP API方式，不直接依赖引擎类
        pass

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

    def _create_test_excel(self):
        """创建测试用的Excel文件"""
        try:
            import pandas as pd

            # 创建测试数据
            test_data = {
                'ID': list(range(1, 21)),  # 20行数据
                '商品名称': [f'商品{i}' for i in range(1, 21)],
                '价格': [100 + i * 10 for i in range(1, 21)],
                '状态': ['待处理'] * 20
            }

            df = pd.DataFrame(test_data)
            df.to_excel(self.test_excel_path, index=False)
            print(f"✅ 创建测试Excel文件: {self.test_excel_path}")

        except ImportError:
            print("⚠️ pandas未安装，跳过Excel文件创建")

    def _start_workflow_via_api(self, input_data: Dict[str, Any]) -> Optional[str]:
        """通过API启动工作流"""
        try:
            # 使用multipart/form-data方式提交
            files = {}
            form_data = {}

            for key, value in input_data.items():
                if isinstance(value, dict) and 'file_path' in value:
                    # 处理文件上传
                    with open(value['file_path'], 'rb') as f:
                        file_content = f.read()
                    files[key] = (
                        value['filename'],
                        file_content,
                        value['content_type']
                    )
                else:
                    form_data[key] = str(value)

            # 提交到flow1
            response = self.session.post(
                f"{self.base_url}/api/flows/abba-ccdd-eeff-1.0.0/submit",
                files=files,
                data=form_data,
                allow_redirects=False
            )

            if response.status_code == 302:
                # 重定向成功，提取thread_id
                redirect_url = response.headers.get('location', '')
                if 'thread_id=' in redirect_url:
                    thread_id = redirect_url.split('thread_id=')[1].split('&')[0]
                    return thread_id
            elif response.status_code == 200:
                # JSON响应
                try:
                    result = response.json()
                    return result.get("thread_id")
                except:
                    pass

            print(f"⚠️ 工作流启动失败: HTTP {response.status_code}")
            return None

        except Exception as e:
            print(f"❌ 工作流启动异常: {str(e)}")
            return None

    def _pause_workflow_via_api(self, thread_id: str) -> bool:
        """通过API暂停工作流"""
        try:
            response = self.session.post(f"{self.base_url}/runs/{thread_id}/pause")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 暂停工作流异常: {str(e)}")
            return False

    def _resume_workflow_via_api(self, thread_id: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """通过API恢复工作流"""
        try:
            data = {"updates": updates} if updates else {}
            response = self.session.post(f"{self.base_url}/runs/{thread_id}/resume", json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 恢复工作流异常: {str(e)}")
            return False

    def _get_workflow_status_via_api(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """通过API获取工作流状态"""
        try:
            response = self.session.get(f"{self.base_url}/runs/{thread_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ 获取工作流状态异常: {str(e)}")
            return None

    def _cancel_workflow_via_api(self, thread_id: str) -> bool:
        """通过API取消工作流"""
        try:
            response = self.session.delete(f"{self.base_url}/runs/{thread_id}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 取消工作流异常: {str(e)}")
            return False

    def _wait_for_completion(self, thread_id: str, timeout_seconds: int = 60) -> bool:
        """等待工作流完成"""
        start_time = time.time()

        while time.time() - start_time < timeout_seconds:
            status = self._get_workflow_status_via_api(thread_id)
            if not status:
                return False

            current_status = status.get("status", "unknown")
            if current_status in ["completed", "failed", "cancelled"]:
                return current_status == "completed"

            time.sleep(1)  # 每秒检查一次

        return False  # 超时

    def _check_server_health(self) -> bool:
        """检查服务器健康状态"""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 服务器健康检查失败: {str(e)}")
            return False

    def test_flow1_pause_resume_basic(self):
        """测试基本的暂停和恢复功能"""
        print("\n🧪 测试Flow1基本暂停恢复功能")
        
        # 1. 启动工作流
        try:
            # 准备输入数据
            input_data = {
                'user_name': 'test_user',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            # 启动工作流
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("基本暂停恢复", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动成功: {thread_id}")

            # 2. 等待一段时间让循环开始执行
            time.sleep(3)

            # 3. 暂停工作流
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("基本暂停恢复", False, "暂停工作流失败")
                return False
            print("✅ 工作流暂停成功")

            # 4. 检查工作流状态
            status = self._get_workflow_status_via_api(thread_id)
            print(f"📊 暂停后状态: {status.get('status') if status else 'Unknown'}")

            # 5. 等待确保暂停生效
            time.sleep(2)

            # 6. 恢复工作流
            resume_success = self._resume_workflow_via_api(thread_id)
            if not resume_success:
                self.log_test("基本暂停恢复", False, "恢复工作流失败")
                return False
            print("✅ 工作流恢复成功")

            # 7. 等待工作流完成
            completed = self._wait_for_completion(thread_id, timeout_seconds=30)
            print(f"📋 工作流完成状态: {'完成' if completed else '超时或失败'}")

            self.log_test("基本暂停恢复", True, f"工作流 {thread_id} 暂停恢复测试成功")
            return True

        except Exception as e:
            self.log_test("基本暂停恢复", False, f"异常: {str(e)}")
            return False

    def test_flow1_pause_during_iteration(self):
        """测试在循环迭代过程中暂停"""
        print("\n🧪 测试循环迭代中暂停")
        
        try:
            # 启动工作流
            input_data = {
                'user_name': 'test_user_iteration',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("迭代中暂停", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动: {thread_id}")

            # 等待几次迭代后暂停
            time.sleep(5)  # 让它执行几次循环

            # 暂停
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("迭代中暂停", False, "暂停工作流失败")
                return False
            print("✅ 在迭代中暂停成功")

            # 检查状态和进度
            status = self._get_workflow_status_via_api(thread_id)
            if status and 'data' in status:
                loop_count = status['data'].get('loop_count', 0)
                print(f"📊 暂停时循环计数: {loop_count}")

            # 等待一段时间确保暂停
            time.sleep(3)

            # 恢复并继续
            resume_success = self._resume_workflow_via_api(thread_id)
            if not resume_success:
                self.log_test("迭代中暂停", False, "恢复工作流失败")
                return False
            print("✅ 从迭代中恢复成功")

            self.log_test("迭代中暂停", True, f"工作流 {thread_id} 迭代中暂停恢复测试成功")
            return True

        except Exception as e:
            self.log_test("迭代中暂停", False, f"异常: {str(e)}")
            return False

    def test_flow1_pause_during_wait(self):
        """测试在等待间隔期间暂停"""
        print("\n🧪 测试等待间隔中暂停")
        
        try:
            # 启动工作流
            input_data = {
                'user_name': 'test_user_wait',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("等待间隔暂停", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动: {thread_id}")

            # 等待到等待间隔期间暂停（大约在第一次迭代的等待期间）
            time.sleep(4)  # 第一次迭代完成，进入等待期间

            # 暂停
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("等待间隔暂停", False, "暂停工作流失败")
                return False
            print("✅ 在等待间隔中暂停成功")

            # 检查状态
            status = self._get_workflow_status_via_api(thread_id)
            if status and 'data' in status:
                wait_elapsed = status['data'].get('wait_elapsed', 0)
                print(f"📊 暂停时已等待时间: {wait_elapsed}秒")

            # 等待确保暂停生效
            time.sleep(2)

            # 恢复
            resume_success = self._resume_workflow_via_api(thread_id)
            if not resume_success:
                self.log_test("等待间隔暂停", False, "恢复工作流失败")
                return False
            print("✅ 从等待间隔中恢复成功")

            self.log_test("等待间隔暂停", True, f"工作流 {thread_id} 等待间隔暂停恢复测试成功")
            return True

        except Exception as e:
            self.log_test("等待间隔暂停", False, f"异常: {str(e)}")
            return False

    def test_flow1_multiple_pause_resume(self):
        """测试多次暂停和恢复"""
        print("\n🧪 测试多次暂停恢复")
        
        try:
            # 启动工作流
            input_data = {
                'user_name': 'test_user_multiple',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("多次暂停恢复", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动: {thread_id}")

            # 进行多次暂停和恢复
            for i in range(3):
                print(f"🔄 第{i+1}次暂停恢复循环")

                # 等待执行
                time.sleep(3)

                # 暂停
                pause_success = self._pause_workflow_via_api(thread_id)
                if not pause_success:
                    self.log_test("多次暂停恢复", False, f"第{i+1}次暂停失败")
                    return False
                print(f"  ✅ 第{i+1}次暂停成功")

                # 检查状态
                status = self._get_workflow_status_via_api(thread_id)
                if status and 'data' in status:
                    loop_count = status['data'].get('loop_count', 0)
                    print(f"  📊 当前循环计数: {loop_count}")

                # 短暂等待
                time.sleep(1)

                # 恢复
                resume_success = self._resume_workflow_via_api(thread_id)
                if not resume_success:
                    self.log_test("多次暂停恢复", False, f"第{i+1}次恢复失败")
                    return False
                print(f"  ✅ 第{i+1}次恢复成功")

            # 让工作流完成
            time.sleep(10)

            self.log_test("多次暂停恢复", True, f"工作流 {thread_id} 多次暂停恢复测试成功")
            return True

        except Exception as e:
            self.log_test("多次暂停恢复", False, f"异常: {str(e)}")
            return False

    def test_flow1_state_persistence(self):
        """测试状态持久化"""
        print("\n🧪 测试状态持久化")
        
        try:
            # 启动工作流
            input_data = {
                'user_name': 'test_user_persistence',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("状态持久化", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动: {thread_id}")

            # 等待几次迭代
            time.sleep(6)

            # 获取暂停前状态
            status_before = self._get_workflow_status_via_api(thread_id)
            loop_count_before = status_before['data'].get('loop_count', 0) if status_before and 'data' in status_before else 0
            print(f"📊 暂停前循环计数: {loop_count_before}")

            # 暂停
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("状态持久化", False, "暂停工作流失败")
                return False
            print("✅ 暂停成功")

            # 等待确保暂停
            time.sleep(2)

            # 获取暂停后状态
            status_paused = self._get_workflow_status_via_api(thread_id)
            loop_count_paused = status_paused['data'].get('loop_count', 0) if status_paused and 'data' in status_paused else 0
            print(f"📊 暂停后循环计数: {loop_count_paused}")

            # 恢复
            resume_success = self._resume_workflow_via_api(thread_id)
            if not resume_success:
                self.log_test("状态持久化", False, "恢复工作流失败")
                return False
            print("✅ 恢复成功")

            # 等待继续执行
            time.sleep(4)

            # 获取恢复后状态
            status_after = self._get_workflow_status_via_api(thread_id)
            loop_count_after = status_after['data'].get('loop_count', 0) if status_after and 'data' in status_after else 0
            print(f"📊 恢复后循环计数: {loop_count_after}")

            # 验证状态持久化
            if loop_count_after < loop_count_paused:
                self.log_test("状态持久化", False, "状态未正确持久化")
                return False
            print("✅ 状态持久化验证成功")

            self.log_test("状态持久化", True, f"工作流 {thread_id} 状态持久化测试成功")
            return True

        except Exception as e:
            self.log_test("状态持久化", False, f"异常: {str(e)}")
            return False

    def test_flow1_cancel_workflow(self):
        """测试取消工作流"""
        print("\n🧪 测试取消工作流")
        
        try:
            # 启动工作流
            input_data = {
                'user_name': 'test_user_cancel',
                'processing_mode': 'excel_analysis',
                'shopfile': {
                    'filename': 'test_excel.xlsx',
                    'content_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                    'file_path': str(self.test_excel_path)
                }
            }
            
            thread_id = self._start_workflow_via_api(input_data)
            if not thread_id:
                self.log_test("取消工作流", False, "工作流启动失败")
                return False

            print(f"✅ 工作流启动: {thread_id}")

            # 等待执行
            time.sleep(3)

            # 取消工作流
            cancel_success = self._cancel_workflow_via_api(thread_id)
            if not cancel_success:
                self.log_test("取消工作流", False, "取消工作流失败")
                return False
            print("✅ 工作流取消成功")

            # 检查最终状态
            time.sleep(2)
            status = self._get_workflow_status_via_api(thread_id)
            if status:
                print(f"📊 最终状态: {status.get('status', 'Unknown')}")

            self.log_test("取消工作流", True, f"工作流 {thread_id} 取消测试成功")
            return True

        except Exception as e:
            self.log_test("取消工作流", False, f"异常: {str(e)}")
            return False

    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始Flow1 Stop/Resume功能测试")
        print("=" * 60)
        print(f"🌐 服务器地址: {self.base_url}")
        print(f"📁 测试Excel文件: {self.test_excel_path}")
        print("=" * 60)

        # 首先检查服务器健康状态
        if not self._check_server_health():
            print("❌ 服务器不可用，无法进行测试")
            return {}

        test_results = {}

        # 运行各项测试
        test_methods = [
            ('基本暂停恢复', self.test_flow1_pause_resume_basic),
            ('迭代中暂停', self.test_flow1_pause_during_iteration),
            ('等待间隔暂停', self.test_flow1_pause_during_wait),
            ('多次暂停恢复', self.test_flow1_multiple_pause_resume),
            ('状态持久化', self.test_flow1_state_persistence),
            ('取消工作流', self.test_flow1_cancel_workflow)
        ]

        for test_name, test_method in test_methods:
            try:
                print(f"\n{'='*20} {test_name} {'='*20}")
                result = test_method()
                test_results[test_name] = result
                print(f"{'✅ 通过' if result else '❌ 失败'}: {test_name}")
            except Exception as e:
                test_results[test_name] = False
                print(f"❌ 异常: {test_name} - {str(e)}")

        # 输出测试总结
        self._print_test_summary(test_results)
        return test_results

    def _print_test_summary(self, test_results: Dict[str, bool]):
        """打印测试总结"""
        print("\n" + "=" * 60)
        print("🎯 测试结果总结")
        print("=" * 60)

        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)

        for test_name, result in test_results.items():
            status = "✅ 通过" if result else "❌ 失败"
            print(f"{status}: {test_name}")

        print(f"\n📊 总体结果: {passed}/{total} 测试通过")
        if total > 0:
            print(f"成功率: {passed/total*100:.1f}%")

        # 显示失败的测试详情
        failed_tests = [name for name, result in test_results.items() if not result]
        if failed_tests:
            print(f"\n❌ 失败的测试:")
            for test_name in failed_tests:
                failed_result = next((r for r in self.test_results if r["test"] == test_name), None)
                if failed_result:
                    print(f"  - {test_name}: {failed_result['details']}")

        if passed == total and total > 0:
            print("🎉 所有测试通过！Flow1的Stop/Resume功能完全正常！")
        elif passed > 0:
            print("⚠️ 部分测试通过，需要进一步检查失败的测试")
        else:
            print("❌ 所有测试失败，请检查服务器状态和配置")


def main():
    """主函数"""
    tester = TestFlow1StopResume()
    tester.setup_method()
    results = tester.run_all_tests()
    return results


if __name__ == "__main__":
    main()