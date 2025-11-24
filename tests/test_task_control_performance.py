import time
import unittest
from task_manager.mixins import TaskControlMixin

class TestTaskControlPerformance(unittest.TestCase):
    """测试任务控制性能"""
    
    def test_check_task_control_performance(self):
        """测试任务控制点检查性能"""
        # 创建TaskControlMixin实例
        class TestMixin(TaskControlMixin):
            pass
            
        mixin = TestMixin()
        task_id = "performance_test_task"
        
        # 预热
        for _ in range(100):
            mixin._check_task_control(task_id)
            
        # 性能测试
        start_time = time.perf_counter()
        iterations = 10000
        
        for _ in range(iterations):
            mixin._check_task_control(task_id)
            
        end_time = time.perf_counter()
        total_time = end_time - start_time
        avg_time = (total_time / iterations) * 1000  # 转换为毫秒
        
        print(f"执行 {iterations} 次检查耗时: {total_time:.6f} 秒")
        print(f"平均每次检查耗时: {avg_time:.6f} 毫秒")
        
        # 验证性能是否小于1ms
        self.assertLess(avg_time, 1.0, f"任务控制点检查应该小于1ms，实际平均时间: {avg_time:.6f}ms")

if __name__ == '__main__':
    unittest.main()