"""Flow1 具体业务节点实现"""

import time
from datetime import datetime
from typing import Any, Dict
from src_new.workflow_engine.core.registry import register_function
from src_new.workflow_engine.core.models import WorkflowState
from src_new.workflow_engine.utils.logger import WorkflowLogger


@register_function("flow1.loop_node")
def loop_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """循环节点实现：执行指定次数的循环操作
    
    Args:
        iterations: 循环次数，默认1次
        interval_seconds: 每次循环间隔时间，默认2.0秒
    """
    iterations = kwargs.get('iterations', 1)
    interval_seconds = kwargs.get('interval_seconds', 2.0)
    
    # 获取当前循环进度
    current_iteration = state.data.get('current_iteration', 0)
    
    logger.info(f"开始循环节点执行，总次数: {iterations}, 间隔: {interval_seconds}秒", 
               node_id="loop_node",
               context={"iterations": iterations, "interval": interval_seconds})
    
    # 执行循环
    for i in range(current_iteration, iterations):
        # 检查暂停请求
        if state.pause_requested:
            logger.info(f"循环在第 {i+1} 次时暂停")
            interrupt_fn(f"Loop paused at iteration {i+1}", 
                        update={"current_iteration": i})
            return {"current_iteration": i, "paused": True}
        
        # 执行循环操作
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"执行第 {i+1}/{iterations} 次循环，当前时间: {current_time}",
                   node_id="loop_node",
                   context={"iteration": i+1, "total": iterations, "time": current_time})
        
        # 更新状态
        state.data["current_iteration"] = i + 1
        state.data["last_loop_time"] = current_time
        
        # 间隔等待（支持暂停）
        if interval_seconds > 0 and i < iterations - 1:  # 最后一次循环不需要等待
            elapsed = 0.0
            while elapsed < interval_seconds:
                if state.pause_requested:
                    logger.info(f"循环在等待期间暂停")
                    interrupt_fn(f"Loop paused during interval", 
                                update={"current_iteration": i + 1})
                    return {"current_iteration": i + 1, "paused": True}
                
                sleep_time = min(0.1, interval_seconds - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
    
    logger.info(f"循环节点执行完成，共执行 {iterations} 次", 
               node_id="loop_node")
    
    return {
        "iterations_completed": iterations,
        "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_iterations": iterations
    }


@register_function("flow1.delay_node")
def delay_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """延时节点实现：等待指定时间后输出消息
    
    Args:
        delay_seconds: 延时秒数，默认10.0秒
        message: 延时完成后输出的消息，默认"done"
    """
    delay_seconds = kwargs.get('delay_seconds', 10.0)
    message = kwargs.get('message', 'done')
    
    # 获取延时进度
    delay_start_time = state.data.get('delay_start_time')
    if not delay_start_time:
        delay_start_time = time.time()
        state.data['delay_start_time'] = delay_start_time
    
    logger.info(f"开始延时节点执行，延时: {delay_seconds}秒, 消息: '{message}'", 
               node_id="delay_node",
               context={"delay": delay_seconds, "message": message})
    
    # 执行延时等待
    while True:
        current_time = time.time()
        current_elapsed = current_time - delay_start_time
        
        # 检查是否完成
        if current_elapsed >= delay_seconds:
            break
            
        # 检查暂停请求
        if state.pause_requested:
            logger.info(f"延时节点暂停，已等待 {current_elapsed:.1f}/{delay_seconds}秒")
            interrupt_fn(f"Delay paused at {current_elapsed:.1f}s", 
                        update={
                            "delay_start_time": delay_start_time,
                            "delay_elapsed": current_elapsed
                        })
            return {
                "delay_elapsed": current_elapsed,
                "delay_remaining": delay_seconds - current_elapsed,
                "paused": True
            }
        
        # 短暂休眠
        time.sleep(0.1)
    
    # 延时完成，输出消息
    completion_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    logger.info(f"延时节点执行完成: {message}", 
               node_id="delay_node",
               context={"message": message, "completion_time": completion_time})
    
    return {
        "delay_completed": True,
        "delay_seconds": delay_seconds,
        "message": message,
        "completion_time": completion_time
    }