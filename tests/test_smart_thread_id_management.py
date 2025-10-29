"""
测试智能thread_id管理逻辑

验证以下行为：
1. 任务暂停 -> 任务开始：不能产生新的thread_id（复用原有thread_id）
2. 任务取消（停止）-> 任务开始：需要产生新的thread_id
"""

import pytest
import uuid
import time
from unittest.mock import Mock, patch
import sys
import os

# Add the src_new directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src_new'))

from workflow_engine.core.engine import WorkflowEngine
from workflow_engine.core.models import WorkflowDefinition, WorkflowNode, NodeType, PythonNodeData
from workflow_engine.storage.database import DatabaseManager


class TestSmartThreadIdManagement:
    """测试智能thread_id管理功能"""
    
    @pytest.fixture
    def db_manager(self):
        """创建测试数据库管理器"""
        # 使用内存数据库进行测试
        db_manager = DatabaseManager(":memory:")
        return db_manager
    
    @pytest.fixture
    def workflow_engine(self, db_manager):
        """创建工作流引擎实例"""
        return WorkflowEngine(db_manager)
    
    @pytest.fixture
    def sample_workflow_definition(self):
        """创建示例工作流定义"""
        return WorkflowDefinition(
            nodes=[
                WorkflowNode(
                    id="start",
                    type=NodeType.START,
                    data=None
                ),
                WorkflowNode(
                    id="task1",
                    type=NodeType.PYTHON,
                    data=PythonNodeData(
                        code="import time; time.sleep(0.1); return {'result': 'task1_done'}"
                    )
                ),
                WorkflowNode(
                    id="end",
                    type=NodeType.END,
                    data=None
                )
            ],
            edges=[
                {"source": "start", "target": "task1"},
                {"source": "task1", "target": "end"}
            ]
        )
    
    @pytest.fixture
    def flow_version_id(self, workflow_engine, sample_workflow_definition):
        """创建并返回工作流版本ID"""
        return workflow_engine.create_flow("test_flow", sample_workflow_definition)
    
    def test_pause_resume_reuses_thread_id(self, workflow_engine, flow_version_id):
        """测试：暂停后恢复应该复用原有的thread_id"""
        
        # 第一次启动工作流（不提供thread_id，应该生成新的）
        thread_id_1 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证生成了thread_id
        assert thread_id_1 is not None
        assert isinstance(thread_id_1, str)
        
        # 暂停工作流
        success = workflow_engine.pause_workflow(thread_id_1)
        assert success is True
        
        # 等待暂停生效
        time.sleep(0.1)
        
        # 验证工作流状态为暂停
        status = workflow_engine.get_workflow_status(thread_id_1)
        assert status is not None
        assert status.get("status") == "paused"
        
        # 再次启动工作流（不提供thread_id，应该复用暂停的thread_id）
        thread_id_2 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证复用了相同的thread_id
        assert thread_id_2 == thread_id_1
        print(f"✅ 暂停恢复测试通过：复用了thread_id {thread_id_1}")
    
    def test_cancel_restart_generates_new_thread_id(self, workflow_engine, flow_version_id):
        """测试：取消后重启应该生成新的thread_id"""
        
        # 第一次启动工作流
        thread_id_1 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证生成了thread_id
        assert thread_id_1 is not None
        assert isinstance(thread_id_1, str)
        
        # 取消工作流（通过创建取消信号）
        signal_id = workflow_engine.db_manager.create_signal(thread_id_1, "cancel_request")
        assert signal_id is not None
        
        # 等待取消生效
        time.sleep(0.1)
        
        # 手动更新状态为已取消（模拟工作流引擎处理取消信号）
        success = workflow_engine.db_manager.atomic_update_run_status(
            thread_id_1, "running", "cancelled", {"cancel_reason": "Test cancellation"}
        )
        assert success is True
        
        # 验证工作流状态为已取消
        status = workflow_engine.get_workflow_status(thread_id_1)
        assert status is not None
        assert status.get("status") == "cancelled"
        
        # 再次启动工作流（不提供thread_id，应该生成新的thread_id）
        thread_id_2 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证生成了新的thread_id
        assert thread_id_2 != thread_id_1
        assert thread_id_2 is not None
        assert isinstance(thread_id_2, str)
        print(f"✅ 取消重启测试通过：生成了新的thread_id {thread_id_2}（原thread_id: {thread_id_1}）")
    
    def test_completed_restart_generates_new_thread_id(self, workflow_engine, flow_version_id):
        """测试：完成后重启应该生成新的thread_id"""
        
        # 第一次启动工作流
        thread_id_1 = workflow_engine.start_workflow(flow_version_id)
        
        # 手动设置为完成状态
        success = workflow_engine.db_manager.atomic_update_run_status(
            thread_id_1, "running", "completed"
        )
        assert success is True
        
        # 验证工作流状态为已完成
        status = workflow_engine.get_workflow_status(thread_id_1)
        assert status is not None
        assert status.get("status") == "completed"
        
        # 再次启动工作流（不提供thread_id，应该生成新的thread_id）
        thread_id_2 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证生成了新的thread_id
        assert thread_id_2 != thread_id_1
        print(f"✅ 完成重启测试通过：生成了新的thread_id {thread_id_2}（原thread_id: {thread_id_1}）")
    
    def test_failed_restart_generates_new_thread_id(self, workflow_engine, flow_version_id):
        """测试：失败后重启应该生成新的thread_id"""
        
        # 第一次启动工作流
        thread_id_1 = workflow_engine.start_workflow(flow_version_id)
        
        # 手动设置为失败状态
        success = workflow_engine.db_manager.atomic_update_run_status(
            thread_id_1, "running", "failed", {"error": "Test failure"}
        )
        assert success is True
        
        # 验证工作流状态为失败
        status = workflow_engine.get_workflow_status(thread_id_1)
        assert status is not None
        assert status.get("status") == "failed"
        
        # 再次启动工作流（不提供thread_id，应该生成新的thread_id）
        thread_id_2 = workflow_engine.start_workflow(flow_version_id)
        
        # 验证生成了新的thread_id
        assert thread_id_2 != thread_id_1
        print(f"✅ 失败重启测试通过：生成了新的thread_id {thread_id_2}（原thread_id: {thread_id_1}）")
    
    def test_explicit_thread_id_always_used(self, workflow_engine, flow_version_id):
        """测试：显式提供thread_id时总是使用提供的值"""
        
        # 使用显式的thread_id启动工作流
        explicit_thread_id = f"test_thread_{uuid.uuid4().hex[:8]}"
        thread_id = workflow_engine.start_workflow(flow_version_id, thread_id=explicit_thread_id)
        
        # 验证使用了显式提供的thread_id
        assert thread_id == explicit_thread_id
        print(f"✅ 显式thread_id测试通过：使用了提供的thread_id {explicit_thread_id}")


if __name__ == "__main__":
    # 运行测试
    pytest.main([__file__, "-v", "-s"])