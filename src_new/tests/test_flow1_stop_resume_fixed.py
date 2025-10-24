"""Flow1 Stop/Resume 功能测试

这个测试文件验证Flow1工作流的暂停和恢复功能是否正常工作。
测试通过HTTP API调用方式进行，不依赖直接的引擎调用。
"""

import time
import json
import requests
from pathlib import Path
from typing import Dict, Any, Optional

# 尝试导入pandas用于创建Excel文件
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

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
        print(f"🔧 测试环境设置完成")

    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": time.time()
        }
        self.test_results.append(result)

    def _create_test_excel(self):
        """创建测试用的Excel文件"""
        try:
            if not HAS_PANDAS:
                print("⚠️ pandas未安装，跳过Excel文件创建")
                return

            # 创建简单的测试数据
            test_data = {
                'Product': ['Product A', 'Product B', 'Product C', 'Product D', 'Product E'],
                'Price': [10.99, 25.50, 15.75, 8.99, 32.00],
                'Category': ['Electronics', 'Clothing', 'Books', 'Food', 'Electronics'],
                'Stock': [100, 50, 200, 75, 25]
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
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/pause")
            print(f"🔍 暂停API响应: HTTP {response.status_code}")
            if response.status_code != 200:
                try:
                    error_data = response.json()
                    print(f"❌ 暂停失败详情: {error_data}")
                except:
                    print(f"❌ 暂停失败响应: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 暂停工作流异常: {str(e)}")
            return False

    def _resume_workflow_via_api(self, thread_id: str, updates: Optional[Dict[str, Any]] = None) -> bool:
        """通过API恢复工作流"""
        try:
            data = {"updates": updates} if updates else {}
            response = self.session.post(f"{self.base_url}/api/runs/{thread_id}/resume", json=data)
            return response.status_code == 200
        except Exception as e:
            print(f"❌ 恢复工作流异常: {str(e)}")
            return False

    def _get_workflow_status_via_api(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """通过API获取工作流状态"""
        try:
            response = self.session.get(f"{self.base_url}/api/runs/{thread_id}")
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            print(f"❌ 获取工作流状态异常: {str(e)}")
            return None

    def _cancel_workflow_via_api(self, thread_id: str) -> bool:
        """通过API取消工作流"""
        try:
            response = self.session.delete(f"{self.base_url}/api/runs/{thread_id}")
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
                assert False, "工作流启动失败"

            print(f"✅ 工作流启动成功: {thread_id}")

            # 2. 立即尝试暂停（工作流可能很快完成）
            time.sleep(0.5)

            # 3. 暂停工作流
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("基本暂停恢复", False, "暂停工作流失败")
                assert False, "暂停工作流失败"
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
                assert False, "恢复工作流失败"
            print("✅ 工作流恢复成功")

            # 7. 等待工作流完成
            completed = self._wait_for_completion(thread_id, timeout_seconds=30)
            print(f"📋 工作流完成状态: {'完成' if completed else '超时或失败'}")

            self.log_test("基本暂停恢复", True, f"工作流 {thread_id} 暂停恢复测试成功")

        except Exception as e:
            self.log_test("基本暂停恢复", False, f"异常: {str(e)}")
            assert False, f"测试异常: {str(e)}"

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
                assert False, "工作流启动失败"

            print(f"✅ 工作流启动: {thread_id}")

            # 等待几次迭代后暂停
            time.sleep(5)  # 让它执行几次循环

            # 暂停
            pause_success = self._pause_workflow_via_api(thread_id)
            if not pause_success:
                self.log_test("迭代中暂停", False, "暂停工作流失败")
                assert False, "暂停工作流失败"
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
                assert False, "恢复工作流失败"
            print("✅ 从迭代中恢复成功")

            self.log_test("迭代中暂停", True, f"工作流 {thread_id} 迭代中暂停恢复测试成功")

        except Exception as e:
            self.log_test("迭代中暂停", False, f"异常: {str(e)}")
            assert False, f"测试异常: {str(e)}"

    def test_server_health(self):
        """测试服务器健康状态"""
        print("\n🧪 测试服务器健康状态")
        
        health_ok = self._check_server_health()
        if not health_ok:
            self.log_test("服务器健康检查", False, "服务器不可用")
            assert False, "服务器不可用，无法进行测试"
        
        print("✅ 服务器健康状态正常")
        self.log_test("服务器健康检查", True, "服务器正常运行")