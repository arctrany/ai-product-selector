"""Flow2 具体业务节点实现"""

import time
from datetime import datetime
from typing import Any, Dict
from workflow_engine.core.registry import register_function
from workflow_engine.core.models import WorkflowState
from workflow_engine.utils.logger import WorkflowLogger

@register_function("flow2.process_node")
def process_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """数据处理节点实现：批量处理数据
    
    支持细粒度的暂停/恢复控制
    """
    batch_size = kwargs.get('batch_size', 5)
    process_delay = kwargs.get('process_delay', 1.0)
    
    # 获取当前处理进度
    processed_count = state.data.get('processed_count', 0)
    total_items = state.data.get('total_items', batch_size)
    
    logger.info(f"Starting data processing, batch_size: {batch_size}, delay: {process_delay}s", 
               node_id="process_node",
               context={"processed": processed_count, "total": total_items})
    
    # 模拟数据处理
    for i in range(processed_count, total_items):
        # 检查暂停请求
        if state.pause_requested:
            logger.info(f"Processing paused at item {i+1}/{total_items}")
            interrupt_fn(f"Process node paused at item {i+1}", 
                        update={"processed_count": i})
            return {"processed_count": i, "paused": True}
        
        # 模拟处理单个数据项
        logger.info(f"Processing item {i+1}/{total_items}",
                   node_id="process_node",
                   context={"item": i+1, "total": total_items})
        
        # 更新状态
        state.data["processed_count"] = i + 1
        state.data["last_processed_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 处理延时
        if process_delay > 0:
            elapsed = 0.0
            while elapsed < process_delay:
                if state.pause_requested:
                    logger.info(f"Processing paused during delay at item {i+1}")
                    interrupt_fn(f"Process node paused during delay", 
                                update={"processed_count": i + 1})
                    return {"processed_count": i + 1, "paused": True}
                
                sleep_time = min(0.1, process_delay - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time
    
    # 模拟处理结果（90%成功率）
    import random
    process_success = random.random() > 0.1
    
    logger.info(f"Data processing completed: {total_items} items, success: {process_success}", 
               node_id="process_node")
    
    return {
        "processed_count": total_items,
        "process_success": process_success,
        "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_processed": total_items
    }

@register_function("flow2.notify_node")
def notify_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """通知节点实现：发送成功通知
    """
    notification_type = kwargs.get('notification_type', 'success')
    message = kwargs.get('message', 'Processing completed')
    
    logger.info(f"Sending notification: {notification_type} - {message}", 
               node_id="notify_node",
               context={"type": notification_type, "message": message})
    
    # 模拟发送通知
    time.sleep(0.5)
    
    notification_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    return {
        "notification_sent": True,
        "notification_type": notification_type,
        "notification_message": message,
        "notification_time": notification_time
    }

@register_function("flow2.error_node")
def error_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """错误处理节点实现：处理失败情况并重试
    """
    retry_count = kwargs.get('retry_count', 3)
    current_retry = state.data.get('current_retry', 0)
    
    logger.info(f"Processing error handling, retry {current_retry + 1}/{retry_count}", 
               node_id="error_node",
               context={"retry": current_retry + 1, "max_retries": retry_count})
    
    # 检查是否还有重试机会
    if current_retry < retry_count:
        # 模拟重试逻辑
        logger.info(f"Attempting retry {current_retry + 1}", node_id="error_node")
        time.sleep(1.0)  # 重试延时
        
        # 模拟重试结果（50%成功率）
        import random
        retry_success = random.random() > 0.5
        
        state.data["current_retry"] = current_retry + 1
        
        if retry_success:
            logger.info(f"Retry {current_retry + 1} succeeded", node_id="error_node")
            return {
                "retry_success": True,
                "retry_count": current_retry + 1,
                "error_resolved": True,
                "resolution_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        else:
            logger.warning(f"Retry {current_retry + 1} failed", node_id="error_node")
            if current_retry + 1 >= retry_count:
                # 所有重试都失败
                return {
                    "retry_success": False,
                    "retry_count": current_retry + 1,
                    "error_resolved": False,
                    "final_failure": True,
                    "failure_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
            else:
                # 还有重试机会，继续
                return {
                    "retry_success": False,
                    "retry_count": current_retry + 1,
                    "error_resolved": False,
                    "will_retry": True
                }
    else:
        # 没有重试机会了
        logger.error(f"All retries exhausted, processing failed", node_id="error_node")
        return {
            "retry_success": False,
            "retry_count": current_retry,
            "error_resolved": False,
            "final_failure": True,
            "failure_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }