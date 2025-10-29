#!/usr/bin/env python3
"""
工作流 Thread ID 管理测试
验证暂停/取消后重新启动的 thread_id 行为
"""

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

# Add project root to Python path for imports
project_root = Path(__file__).resolve().parents[1]
src_path = project_root / "src_new"

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

try:
    from workflow_engine.core.engine import WorkflowEngine
    from workflow_engine.core.config import WorkflowEngineConfig
    from workflow_engine.sdk.control import WorkflowControl
    from workflow_engine.storage.database import DatabaseManager
    from workflow_engine.core.models import WorkflowDefinition, WorkflowNode, NodeType, PythonNodeData, WorkflowEdge
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running from the project root directory")
    sys.exit(1)


class TestWorkflowThreadIdManagement(unittest.TestCase):
    """测试工作流 Thread ID 管理逻辑"""

    def setUp(self):
        """设置测试环境"""
        # 创建临时数据库
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        
        # 创建配置
        self.config = WorkflowEngineConfig()
        self.config.db_path = self.temp_db.name
        
        # 创建引擎和控制器
        self.engine = WorkflowEngine(self.config)
        self.db_manager = DatabaseManager(self.temp_db.name)
        self.control = WorkflowControl(self.db_manager)
        
        # 创建测试工作流
        self.flow_version_id = self._create_test_workflow()

    def tearDown(self):
        """清理测试环境"""
        try:
            Path(self.temp_db.name).unlink(missing_ok=True)
        except Exception:
            pass

    def _create_test_workflow(self) -> int:
        """创建测试工作流"""
        # 创建简单的工作流定义
        workflow_def = WorkflowDefinition(
            name="test_workflow",
            nodes=[
                WorkflowNode(
                    id="start",
                    type=NodeType.START,
                    data=None
                ),
                WorkflowNode(
                    id="simple_task",
                    type=NodeType.PYTHON,
                    data=PythonNodeData(
                        code_ref="test.hello_world",
                        args={}
                    )
                ),
                WorkflowNode(
                    id="end",
                    type=NodeType.END,
                    data=None
                )
            ],
            edges=[
                WorkflowEdge(source="start", target="simple_task"),
                WorkflowEdge(source="simple_task", target="end")
            ]
        )
        
        return self.engine.create_flow("test_workflow", workflow_def)

    def test_pause_resume_should_reuse_thread_id(self):
        """测试：暂停 -> 恢复应该复用相同的 thread_id"""
        print("\n🧪 测试：暂停 -> 恢复应该复用相同的 thread_id")
        
        # 1. 启动工作流
        original_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   📝 原始 thread_id: {original_thread_id}")
        
        # 2. 暂停工作流
        pause_success = self.control.pause_workflow(original_thread_id)
        self.assertTrue(pause_success, "暂停请求应该成功")
        print(f"   ⏸️  工作流已暂停")
        
        # 3. 模拟暂停状态更新
        self.db_manager.atomic_update_run_status(original_thread_id, "running", "paused")
        
        # 4. 验证当前状态
        run_status = self.db_manager.get_run(original_thread_id)
        self.assertEqual(run_status["status"], "paused", "工作流应该处于暂停状态")
        print(f"   ✅ 工作流状态: {run_status['status']}")
        
        # 5. 恢复工作流 - 应该复用相同的 thread_id
        resume_success = self.control.resume_workflow(original_thread_id)
        self.assertTrue(resume_success, "恢复请求应该成功")
        print(f"   ▶️  工作流已恢复，thread_id: {original_thread_id}")
        
        # 6. 验证 thread_id 没有改变
        final_run_status = self.db_manager.get_run(original_thread_id)
        self.assertIsNotNone(final_run_status, "工作流记录应该存在")
        print(f"   ✅ 验证成功：thread_id 保持不变")

    def test_cancel_restart_should_generate_new_thread_id(self):
        """测试：取消 -> 重新启动应该生成新的 thread_id"""
        print("\n🧪 测试：取消 -> 重新启动应该生成新的 thread_id")
        
        # 1. 启动工作流
        original_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   📝 原始 thread_id: {original_thread_id}")
        
        # 2. 取消工作流
        cancel_success = self.control.cancel_workflow(original_thread_id, "用户取消")
        self.assertTrue(cancel_success, "取消请求应该成功")
        print(f"   🛑 工作流已取消")
        
        # 3. 模拟取消状态更新
        self.db_manager.atomic_update_run_status(original_thread_id, "running", "cancelled")
        
        # 4. 验证当前状态
        run_status = self.db_manager.get_run(original_thread_id)
        self.assertEqual(run_status["status"], "cancelled", "工作流应该处于取消状态")
        print(f"   ✅ 工作流状态: {run_status['status']}")
        
        # 5. 重新启动工作流 - 应该生成新的 thread_id
        new_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   🆕 新的 thread_id: {new_thread_id}")
        
        # 6. 验证 thread_id 已经改变
        self.assertNotEqual(original_thread_id, new_thread_id, "新的 thread_id 应该与原来的不同")
        
        # 7. 验证两个工作流记录都存在
        original_run = self.db_manager.get_run(original_thread_id)
        new_run = self.db_manager.get_run(new_thread_id)
        
        self.assertIsNotNone(original_run, "原始工作流记录应该存在")
        self.assertIsNotNone(new_run, "新工作流记录应该存在")
        self.assertEqual(original_run["status"], "cancelled", "原始工作流应该保持取消状态")
        print(f"   ✅ 验证成功：生成了新的 thread_id")

    def test_failed_restart_should_generate_new_thread_id(self):
        """测试：失败 -> 重新启动应该生成新的 thread_id"""
        print("\n🧪 测试：失败 -> 重新启动应该生成新的 thread_id")
        
        # 1. 启动工作流
        original_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   📝 原始 thread_id: {original_thread_id}")
        
        # 2. 模拟工作流失败
        self.db_manager.atomic_update_run_status(original_thread_id, "running", "failed", {"error": "测试失败"})
        
        # 3. 验证当前状态
        run_status = self.db_manager.get_run(original_thread_id)
        self.assertEqual(run_status["status"], "failed", "工作流应该处于失败状态")
        print(f"   ❌ 工作流状态: {run_status['status']}")
        
        # 4. 重新启动工作流 - 应该生成新的 thread_id
        new_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   🆕 新的 thread_id: {new_thread_id}")
        
        # 5. 验证 thread_id 已经改变
        self.assertNotEqual(original_thread_id, new_thread_id, "新的 thread_id 应该与原来的不同")
        print(f"   ✅ 验证成功：生成了新的 thread_id")

    def test_completed_restart_should_generate_new_thread_id(self):
        """测试：完成 -> 重新启动应该生成新的 thread_id"""
        print("\n🧪 测试：完成 -> 重新启动应该生成新的 thread_id")
        
        # 1. 启动工作流
        original_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   📝 原始 thread_id: {original_thread_id}")
        
        # 2. 模拟工作流完成
        self.db_manager.atomic_update_run_status(original_thread_id, "running", "completed")
        
        # 3. 验证当前状态
        run_status = self.db_manager.get_run(original_thread_id)
        self.assertEqual(run_status["status"], "completed", "工作流应该处于完成状态")
        print(f"   ✅ 工作流状态: {run_status['status']}")
        
        # 4. 重新启动工作流 - 应该生成新的 thread_id
        new_thread_id = self.engine.start_workflow(self.flow_version_id, {"test": "data"})
        print(f"   🆕 新的 thread_id: {new_thread_id}")
        
        # 5. 验证 thread_id 已经改变
        self.assertNotEqual(original_thread_id, new_thread_id, "新的 thread_id 应该与原来的不同")
        print(f"   ✅ 验证成功：生成了新的 thread_id")

    def test_smart_thread_id_management_logic(self):
        """测试：智能 thread_id 管理逻辑的完整场景"""
        print("\n🧪 测试：智能 thread_id 管理逻辑")
        
        # 场景1：正常启动
        thread_id_1 = self.engine.start_workflow(self.flow_version_id, {"test": "data1"})
        print(f"   🆕 场景1 - 正常启动: {thread_id_1}")
        
        # 场景2：暂停后恢复（应该复用）
        self.control.pause_workflow(thread_id_1)
        self.db_manager.atomic_update_run_status(thread_id_1, "running", "paused")
        
        # 这里我们需要实现智能的恢复逻辑，而不是直接调用 start_workflow
        # 应该有一个方法来检查是否可以恢复现有的工作流
        run_status = self.db_manager.get_run(thread_id_1)
        if run_status and run_status["status"] == "paused":
            # 暂停状态，应该恢复而不是重新启动
            resume_success = self.control.resume_workflow(thread_id_1)
            self.assertTrue(resume_success)
            print(f"   ▶️  场景2 - 暂停后恢复: {thread_id_1} (复用)")
        
        # 场景3：取消后重新启动（应该生成新的）
        self.control.cancel_workflow(thread_id_1, "测试取消")
        self.db_manager.atomic_update_run_status(thread_id_1, "running", "cancelled")
        
        thread_id_2 = self.engine.start_workflow(self.flow_version_id, {"test": "data2"})
        self.assertNotEqual(thread_id_1, thread_id_2)
        print(f"   🆕 场景3 - 取消后重启: {thread_id_2} (新生成)")
        
        print(f"   ✅ 智能管理验证成功")


def run_thread_id_management_tests():
    """运行 Thread ID 管理测试"""
    print("🚀 开始 Thread ID 管理测试")
    print("=" * 60)
    
    # 创建测试套件
    suite = unittest.TestLoader().loadTestsFromTestCase(TestWorkflowThreadIdManagement)
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print("\n" + "=" * 60)
    if result.wasSuccessful():
        print("✅ 所有 Thread ID 管理测试通过！")
    else:
        print("❌ 部分 Thread ID 管理测试失败")
        for failure in result.failures:
            print(f"   失败: {failure[0]}")
            print(f"   原因: {failure[1]}")
        for error in result.errors:
            print(f"   错误: {error[0]}")
            print(f"   详情: {error[1]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_thread_id_management_tests()
    sys.exit(0 if success else 1)