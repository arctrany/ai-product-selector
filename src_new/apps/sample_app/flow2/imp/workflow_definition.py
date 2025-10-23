"""Flow2 工作流定义 - 使用编码方式定义工作流结构"""

from workflow_engine.sdk import WorkflowBuilder

def create_flow2_workflow():
    """创建 Flow2 工作流定义
    
    工作流包含：
    1. 开始节点
    2. 数据处理节点
    3. 分支节点（检查处理结果）
    4. 通知节点
    5. 结束节点
    """
    
    # 创建工作流构建器
    builder = WorkflowBuilder("flow2")
    
    # 添加开始节点
    builder.add_start_node("start")
    
    # 添加数据处理节点
    builder.add_code_node(
        node_id="process_node",
        function_ref="flow2.process_node",
        args={
            "batch_size": 5,
            "process_delay": 1.0
        }
    )
    
    # 添加分支节点 - 检查处理是否成功
    builder.add_branch_node(
        node_id="check_result_node", 
        condition={
            "==": [
                {"var": "process_success"}, 
                True
            ]
        }
    )
    
    # 添加通知节点
    builder.add_code_node(
        node_id="notify_node",
        function_ref="flow2.notify_node",
        args={
            "notification_type": "success",
            "message": "Flow2 processing completed successfully"
        }
    )
    
    # 添加错误处理节点
    builder.add_code_node(
        node_id="error_node",
        function_ref="flow2.error_node",
        args={
            "retry_count": 3
        }
    )
    
    # 添加结束节点
    builder.add_end_node("end")
    
    # 定义工作流连接
    builder.add_edge("start", "process_node")
    builder.add_edge("process_node", "check_result_node")
    
    # 分支连接：如果处理成功，进入通知节点；否则进入错误处理节点
    builder.add_edge("check_result_node", "notify_node", condition=True)
    builder.add_edge("check_result_node", "error_node", condition=False)
    
    builder.add_edge("notify_node", "end")
    builder.add_edge("error_node", "end")
    
    # 验证工作流
    errors = builder.validate()
    if errors:
        raise ValueError(f"Workflow validation failed: {errors}")
    
    # 构建工作流定义
    return builder.build()

def get_workflow_metadata():
    """获取工作流元数据"""
    return {
        "name": "flow2",
        "version": "1.0.0",
        "description": "示例工作流：数据处理 + 分支判断 + 通知/错误处理",
        "author": "workflow_engine",
        "tags": ["demo", "process", "branch", "notification"],
        "nodes": {
            "process_node": {
                "type": "code",
                "description": "批量数据处理节点"
            },
            "check_result_node": {
                "type": "branch", 
                "description": "检查处理结果是否成功"
            },
            "notify_node": {
                "type": "code",
                "description": "发送成功通知"
            },
            "error_node": {
                "type": "code",
                "description": "错误处理和重试"
            }
        }
    }