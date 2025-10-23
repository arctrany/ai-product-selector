"""Flow1 工作流定义 - 使用编码方式定义工作流结构"""

from workflow_engine.sdk import WorkflowBuilder, setup_environment

# 设置工作流引擎环境（自动配置Python路径）
setup_environment()
# 节点实现通过注册函数机制加载，无需直接导入


def create_flow1_workflow():
    """创建 Flow1 工作流定义
    
    工作流包含：
    1. 开始节点
    2. 循环节点（10次循环，2秒间隔打印时间）
    3. 分支节点（检查循环是否完成）
    4. 延时节点（休眠10s后打印done）
    5. 结束节点
    """
    
    # 创建工作流构建器
    builder = WorkflowBuilder("flow1")
    
    # 添加开始节点
    builder.add_start_node("start")
    
    # 添加循环节点
    builder.add_code_node(
        node_id="loop_node",
        function_ref="flow1.loop_node",
        args={
            "iterations": 10,
            "interval_seconds": 2.0
        }
    )
    
    # 添加分支节点 - 复用现有的 ConditionNode 实现
    builder.add_branch_node(
        node_id="branch_node", 
        condition={
            "==": [
                {"var": "loop_completed"}, 
                True
            ]
        }
    )
    
    # 添加延时节点
    builder.add_code_node(
        node_id="delay_node",
        function_ref="flow1.delay_node",
        args={
            "delay_seconds": 10.0,
            "message": "done"
        }
    )
    
    # 添加结束节点
    builder.add_end_node("end")
    
    # 定义工作流连接
    builder.add_edge("start", "loop_node")
    builder.add_edge("loop_node", "branch_node")
    
    # 分支连接：如果循环完成，进入延时节点；否则回到循环节点
    builder.add_edge("branch_node", "delay_node", condition=True)
    builder.add_edge("branch_node", "loop_node", condition=False)
    
    builder.add_edge("delay_node", "end")
    
    # 验证工作流
    errors = builder.validate()
    if errors:
        raise ValueError(f"Workflow validation failed: {errors}")
    
    # 构建工作流定义
    return builder.build()


# get_workflow_metadata 函数已移除
# 现在系统会自动从 WorkflowDefinition 提取元数据，避免重复定义
# 基本信息从 app.json 获取，节点信息从工作流定义中自动提取