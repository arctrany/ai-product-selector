"""Flow1 具体业务节点实现"""

import time
import os
import io
import base64
from datetime import datetime
from typing import Any, Dict
import pandas as pd
from workflow_engine.sdk import register_function, WorkflowState, WorkflowLogger


def _read_excel_file(file_data: Dict[str, Any], logger: WorkflowLogger) -> pd.DataFrame:
    """从文件路径读取Excel文件数据"""
    try:
        # 获取文件路径
        if 'file_path' in file_data:
            file_path = file_data['file_path']
            logger.info(f"从文件路径读取Excel: {file_path}")

            # 直接使用pandas从文件路径读取Excel文件
            df = pd.read_excel(file_path)
            logger.info(f"成功读取Excel文件，共 {len(df)} 行，{len(df.columns)} 列")
            logger.info(f"列名: {list(df.columns)}")

            return df
        else:
            raise ValueError("文件数据中没有找到file_path字段")

    except Exception as e:
        logger.error(f"读取Excel文件失败: {str(e)}")
        raise


@register_function("flow1.loop_node")
def loop_node_impl(state: WorkflowState, logger: WorkflowLogger, interrupt_fn, **kwargs) -> Dict[str, Any]:
    """循环节点实现：读取Excel文件并循环输出内容

    支持细粒度的暂停/恢复控制
    """
    iterations = kwargs.get('iterations', 10)
    interval_seconds = kwargs.get('interval_seconds', 2.0)

    # 获取当前循环计数
    loop_count = state.data.get('loop_count', 0)

    # 读取表单数据 - 修复LangGraph状态数据访问
    # LangGraph可能直接将input_data作为state.data传递
    form_data = state.data.get('form_data', {})
    input_data = state.data.get('input_data', {})

    # 如果form_data和input_data都为空，检查state.data本身是否包含表单数据
    if not form_data and not input_data and state.data:
        # 直接使用state.data作为输入数据
        all_input_data = state.data
        logger.info(f"Using state.data directly as input: {list(state.data.keys())}")
    else:
        # 合并所有输入数据
        all_input_data = {**form_data, **input_data}

    logger.info(f"Starting loop node with Excel file processing")
    logger.info(f"Form data keys: {list(all_input_data.keys())}")
    logger.info(f"Iterations: {iterations}, interval: {interval_seconds}s")

    # 查找Excel文件并读取
    excel_data = None
    excel_filename = None

    if all_input_data:
        logger.info("=== 检查表单数据中的文件 ===")
        for key, value in all_input_data.items():
            # 处理文件上传数据
            if isinstance(value, dict) and 'filename' in value:
                filename = value.get('filename', '')
                content_type = value.get('content_type', '')
                logger.info(f"发现文件字段 '{key}': {filename} (类型: {content_type})")

                # 检查是否是Excel文件
                if (filename.lower().endswith(('.xlsx', '.xls')) or
                        'excel' in content_type.lower() or
                        'spreadsheet' in content_type.lower()):
                    logger.info(f"检测到Excel文件: {filename}")
                    try:
                        excel_data = _read_excel_file(value, logger)
                        excel_filename = filename
                        break
                    except Exception as e:
                        logger.error(f"读取Excel文件 {filename} 失败: {str(e)}")
            else:
                logger.info(f"表单字段 '{key}': {value}")
        logger.info("=== 表单数据检查结束 ===")
    else:
        logger.info("未检测到表单数据")

    # 如果没有找到Excel文件，使用表单数据
    if excel_data is None:
        logger.info("未找到Excel文件，将使用表单数据进行循环")
        excel_data = pd.DataFrame([all_input_data]) if all_input_data else pd.DataFrame()
        excel_filename = "表单数据"

    # 如果Excel数据为空，创建默认数据
    if excel_data.empty:
        logger.info("没有可处理的数据，创建默认示例数据")
        excel_data = pd.DataFrame({
            'ID': [1, 2, 3],
            '名称': ['示例1', '示例2', '示例3'],
            '状态': ['待处理', '处理中', '已完成']
        })
        excel_filename = "默认示例数据"

    # 显示Excel数据概览
    logger.info(f"=== {excel_filename} 数据概览 ===")
    logger.info(f"数据行数: {len(excel_data)}")
    logger.info(f"数据列数: {len(excel_data.columns)}")
    logger.info(f"列名: {list(excel_data.columns)}")

    # 显示前几行数据
    if len(excel_data) > 0:
        logger.info("前5行数据预览:")
        for idx, row in excel_data.head().iterrows():
            row_data = row.to_dict()
            logger.info(f"  行 {idx + 1}: {row_data}")

    # 根据Excel数据行数调整迭代次数
    data_rows = len(excel_data)
    if data_rows > 0:
        # 使用Excel行数作为迭代次数，但不超过原设定的iterations
        actual_iterations = min(iterations, data_rows)
        logger.info(f"根据Excel数据调整迭代次数为: {actual_iterations}")
    else:
        actual_iterations = iterations

    # 执行循环处理 - 逐行输出Excel数据
    for i in range(loop_count, actual_iterations):
        # 检查暂停请求
        if state.pause_requested:
            logger.info(f"Loop paused at iteration {i + 1}/{actual_iterations}")
            interrupt_fn(f"Loop node paused at iteration {i + 1}",
                         update={"loop_count": i})
            return {"loop_count": i, "paused": True}

        # 执行当前迭代 - 输出Excel行数据
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        logger.info(f"=== 循环第 {i + 1}/{actual_iterations} 次 ===")
        logger.info(f"当前时间: {current_time}")

        # 输出当前行的Excel数据
        if i < len(excel_data):
            current_row = excel_data.iloc[i]
            logger.info(f"处理Excel第 {i + 1} 行数据:")
            for col_name, cell_value in current_row.items():
                logger.info(f"  {col_name}: {cell_value}")

            # 将当前行数据保存到状态中
            state.data[f"current_row_{i + 1}"] = current_row.to_dict()
        else:
            logger.info(f"第 {i + 1} 次循环：超出Excel数据范围，输出表单数据")
            for key, value in all_input_data.items():
                if isinstance(value, dict) and 'filename' in value:
                    logger.info(f"  文件 {key}: {value.get('filename', 'unknown')}")
                else:
                    logger.info(f"  {key}: {value}")

        # 更新状态
        state.data["loop_count"] = i + 1
        state.data["last_iteration_time"] = current_time
        state.data["processed_excel_file"] = excel_filename
        state.data["excel_rows_processed"] = min(i + 1, len(excel_data))

        # 间隔等待（除了最后一次迭代）
        if i < actual_iterations - 1:
            logger.info(f"等待 {interval_seconds} 秒...")
            # 分段等待以支持暂停
            elapsed = 0.0
            while elapsed < interval_seconds:
                if state.pause_requested:
                    logger.info(f"Loop paused during wait at iteration {i + 1}")
                    interrupt_fn(f"Loop node paused during wait",
                                 update={"loop_count": i + 1, "wait_elapsed": elapsed})
                    return {"loop_count": i + 1, "wait_elapsed": elapsed, "paused": True}

                sleep_time = min(0.1, interval_seconds - elapsed)
                time.sleep(sleep_time)
                elapsed += sleep_time

    logger.info(f"Excel数据循环处理完成: {actual_iterations} 次迭代")
    logger.info(f"处理的Excel文件: {excel_filename}")
    logger.info(f"Excel数据行数: {len(excel_data)}")
    logger.info(f"实际处理行数: {min(actual_iterations, len(excel_data))}")

    return {
        "loop_count": actual_iterations,
        "loop_completed": True,
        "completion_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "processed_excel_file": excel_filename,
        "excel_total_rows": len(excel_data),
        "excel_columns": list(excel_data.columns) if not excel_data.empty else [],
        "rows_processed": min(actual_iterations, len(excel_data)),
        "form_fields_count": len(all_input_data)
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
