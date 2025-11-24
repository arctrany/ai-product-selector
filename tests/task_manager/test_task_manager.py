import unittest
import time
from task_manager.controllers import TaskManager
from task_manager.interfaces import ITaskEventListener, TaskInfo, TaskStatus
from task_manager.utils import TaskTimer


class TestTaskManager(unittest.TestCase):
    
    def setUp(self):
        self.task_manager = TaskManager()
        self.events = []
        
    def tearDown(self):
        self.task_manager.shutdown()
        
    def test_create_task(self):
        """测试创建任务"""
        def sample_task():
            return "task completed"
            
        task_id = self.task_manager.create_task("test_task", sample_task)
        self.assertIsNotNone(task_id)
        
        task_info = self.task_manager.get_task_info(task_id)
        self.assertIsNotNone(task_info)
        self.assertEqual(task_info.name, "test_task")
        self.assertEqual(task_info.status, TaskStatus.PENDING)
        
    def test_start_task(self):
        """测试启动任务"""
        def sample_task():
            time.sleep(0.1)
            return "task completed"
            
        task_id = self.task_manager.create_task("test_task", sample_task)
        result = self.task_manager.start_task(task_id)
        self.assertTrue(result)
        
        task_info = self.task_manager.get_task_info(task_id)
        self.assertEqual(task_info.status, TaskStatus.RUNNING)
        
    def test_task_completion(self):
        """测试任务完成"""
        def sample_task():
            return "task completed"
            
        task_id = self.task_manager.create_task("test_task", sample_task)
        self.task_manager.start_task(task_id)
        
        # 等待任务完成
        time.sleep(0.1)
        
        task_info = self.task_manager.get_task_info(task_id)
        self.assertEqual(task_info.status, TaskStatus.COMPLETED)
        self.assertEqual(task_info.progress.percentage, 100.0)
        
    def test_task_failure(self):
        """测试任务失败"""
        def failing_task():
            raise Exception("Task failed")
            
        task_id = self.task_manager.create_task("failing_task", failing_task)
        self.task_manager.start_task(task_id)
        
        # 等待任务失败
        time.sleep(0.1)
        
        task_info = self.task_manager.get_task_info(task_id)
        self.assertEqual(task_info.status, TaskStatus.FAILED)
        self.assertIsNotNone(task_info.error)
        
    def test_stop_task(self):
        """测试停止任务"""
        def long_running_task():
            time.sleep(1)
            return "task completed"
            
        task_id = self.task_manager.create_task("long_task", long_running_task)
        self.task_manager.start_task(task_id)
        
        # 立即停止任务
        result = self.task_manager.stop_task(task_id)
        self.assertTrue(result)
        
        task_info = self.task_manager.get_task_info(task_id)
        self.assertEqual(task_info.status, TaskStatus.STOPPED)


if __name__ == '__main__':
    unittest.main()
