"""Flow1 具体业务节点实现"""

import time
from datetime import datetime
from typing import Any, Dict
from workflow_engine.core.registry import register_function
from workflow_engine.core.models import WorkflowState
from workflow_engine.utils.logger import WorkflowLogger


@register_function("flow1.loop_node")
def loop_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """循环节点实现：循环10次，每间隔2秒打印当前时间
    
    支持细粒度的暂停/恢复控制
    """
    iterations = kwargs.get('iterations', 10)
    interval_seconds = kwargs.get('interval_seconds', 2.0)
    
    # 获取当前循环计数
    loop_count = state.data.get('loop_count', 0)
    
    logger.info(f"Starting loop node, iterations: {iterations}, interval: {interval_seconds}s")
    
    for i in range(loop_count, iterations):
        # 检查暂停请求
        if state.pause_requested:
            logger.info(f"Loop paused at iteration {i+1}/{iterations}")
            interrupt_fn(f"Loop node paused at iteration {i+1}", 
                        update={"loop_count": i})
            return {"loop_count": i, "paused": True}
        
        # 执行当前迭代
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"Loop iteration {i+1}/{iterations} - Current time: {current_time}")
        
        # 更新状态
        state.data["loop_count"] = i + 1
        state.data["last_iteration_time"] = current_time
        
        # 间隔等待（除了最后一次迭代）
        if i < iterations - 1:
            # 分段等待以支持暂停
            elapsed = 0.0
            while elapsed < interval_seconds:
                if state.pause_requested:
                    logger.info(f"Loop paused during wait at iteration {i+1}")
                    interrupt_fn(f"Loop node paused during wait", 
                                update={"loop_count": i + 1, "wait_elapsed": elapsed})
                    return {"loop_count": i + 1, "wait_elapsed": elapsed, "paused": True}
                
                sleep_time = min(0.1, interval_seconds - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
    
    logger.info(f"Loop completed: {iterations} iterations")
    return {
        "loop_count": iterations,
        "loop_completed": True,
        "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }


# 分支节点复用现有的 ConditionNode 实现，不需要重新实现
# 分支逻辑通过 JSONLogic 表达式在工作流定义中配置


@register_function("flow1.delay_node")
def delay_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """延时节点实现：休眠10秒后打印"done"
    
    支持暂停/恢复，可以在延时过程中暂停
    """
    delay_seconds = kwargs.get('delay_seconds', 10.0)
    message = kwargs.get('message', 'done')
    
    # 获取延时状态
    delay_start_time = state.data.get('delay_start_time')
    delay_elapsed = state.data.get('delay_elapsed', 0.0)
    
    if delay_start_time is None:
        # 首次执行
        delay_start_time = time.time()
        state.data['delay_start_time'] = delay_start_time
        logger.info(f"Starting delay of {delay_seconds} seconds")
    else:
        # 从暂停恢复
        logger.info(f"Resuming delay, {delay_seconds - delay_elapsed:.1f} seconds remaining")
    
    # 执行延时
    while delay_elapsed < delay_seconds:
        # 检查暂停请求
        if state.pause_requested:
            current_elapsed = time.time() - delay_start_time
            logger.info(f"Delay paused after {current_elapsed:.1f} seconds")
            interrupt_fn(f"Delay node paused", 
                        update={
                            "delay_start_time": delay_start_time,
                            "delay_elapsed": current_elapsed
                        })
            return {
                "delay_elapsed": current_elapsed,
                "delay_remaining": delay_seconds - current_elapsed,
                "paused": True
            }
        
        # 短暂睡眠以允许暂停检查
        time.sleep(0.1)
        delay_elapsed = time.time() - delay_start_time
    
    # 延时完成
    completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"Delay completed: {message}")
    
    # 清理延时状态
    state.data.pop('delay_start_time', None)
    state.data.pop('delay_elapsed', None)
    
    return {
        "delay_completed": True,
        "delay_message": message,
        "completion_time": completion_time,
        "total_delay": delay_seconds
    }