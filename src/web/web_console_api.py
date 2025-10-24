"""
Web控制台API模块 - 业务逻辑API接口
提供任务管理、浏览器控制、控制台状态等核心API功能
与场景无关的纯业务逻辑，不依赖scenes目录
"""

import os
import json
import asyncio
import threading
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Blueprint, jsonify, Response

from web.web_console import web_console
from playweight.utils.path_config import get_upload_dir

# 创建API蓝图
api_bp = Blueprint('api', __name__, url_prefix='/api')

# 全局变量 - 业务逻辑状态管理
current_task_thread = None
current_form_data = None
task_stop_flag = False
current_runner = None

# 任务执行器接口 - 由具体业务模块实现
_task_executor = None


def register_task_executor(executor):
    """注册任务执行器"""
    global _task_executor
    _task_executor = executor


async def run_automation_task(task_id: str, form_data: Dict[str, Any]):
    """运行自动化任务 - 纯API接口，委托给注册的执行器"""
    global task_stop_flag, current_runner
    task_stop_flag = False

    try:
        if _task_executor is None:
            error_msg = "任务执行器未注册，请检查业务模块初始化"
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        web_console.info(f"开始执行自动化任务: {task_id}")

        # 委托给注册的执行器
        def set_current_runner(runner):
            global current_runner
            current_runner = runner

        await _task_executor.execute_task(task_id, form_data, {
            'task_stop_flag': lambda: task_stop_flag,
            'set_current_runner': set_current_runner,
            'web_console': web_console
        })

    except Exception as e:
        error_msg = f"任务执行失败: {str(e)}"
        web_console.error(error_msg)
        import traceback
        web_console.error(f"错误堆栈: {traceback.format_exc()}")
        web_console.set_task_error(task_id, error_msg)
        current_runner = None


def set_form_data(form_data: Dict[str, Any]):
    """设置表单数据 - 供外部调用"""
    global current_form_data
    current_form_data = form_data.copy()


def get_form_data() -> Optional[Dict[str, Any]]:
    """获取表单数据"""
    return current_form_data


# ==================== 任务管理API ====================

@api_bp.route('/task/start', methods=['POST'])
def start_task():
    """启动任务API"""
    global current_task_thread

    try:
        if web_console.is_task_running():
            return jsonify({'success': False, 'error': '任务已在运行中'}), 400

        if current_form_data is None:
            return jsonify({'success': False, 'error': '没有找到表单数据，请先填写并提交表单'}), 400

        if _task_executor is None:
            return jsonify({'success': False, 'error': '任务执行器未注册，请检查系统初始化'}), 500

        # 让执行器决定任务参数
        task_config = _task_executor.get_task_config(current_form_data) if hasattr(_task_executor,
                                                                                   'get_task_config') else {}

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task_name = task_config.get('name', '自动化任务')
        total_items = task_config.get('total_items', 1)

        task = web_console.create_task(task_id, task_name, total_items=total_items)

        form_data = current_form_data.copy()
        web_console.info(f"📋 使用表单数据启动任务: {list(form_data.keys())}")

        def run_task():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(run_automation_task(task_id, form_data))
            finally:
                loop.close()

        current_task_thread = threading.Thread(target=run_task)
        current_task_thread.daemon = True
        current_task_thread.start()

        return jsonify({'success': True, 'task_id': task_id})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/task/<task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """暂停任务API"""
    try:
        web_console.pause_task(task_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/task/<task_id>/resume', methods=['POST'])
def resume_task(task_id):
    """恢复任务API"""
    try:
        web_console.resume_task(task_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/task/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务API"""
    global task_stop_flag, current_task_thread
    try:
        task_stop_flag = True
        web_console.stop_task(task_id)
        web_console.warning("🛑 用户请求停止任务")

        if current_task_thread and current_task_thread.is_alive():
            web_console.info("等待任务线程结束...")

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 控制台管理API ====================

@api_bp.route('/console/state')
def get_console_state():
    """获取控制台状态API"""
    try:
        state = web_console.get_console_state()
        return jsonify(state)
    except Exception as e:
        error_msg = f"获取控制台状态失败: {str(e)}"
        fallback_state = {
            "messages": [],
            "current_task": {"status": "error", "error": error_msg},
            "all_tasks": [],
            "is_running": False,
            "timestamp": datetime.now().isoformat(),
            "error": error_msg
        }
        return jsonify(fallback_state)


@api_bp.route('/console/clear', methods=['POST'])
def clear_console():
    """清空控制台API"""
    try:
        web_console.clear_messages()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ==================== 浏览器控制API ====================

@api_bp.route('/browser/screenshot', methods=['GET'])
def get_browser_screenshot():
    """获取浏览器截图API"""
    try:
        global current_runner

        # 状态检查
        if not current_runner:
            web_console.warning("截图请求失败: 没有活跃的浏览器会话")
            return jsonify({
                'error': 'No active browser session',
                'detail': 'Task not started or browser not initialized'
            }), 404

        if not hasattr(current_runner, 'browser_service') or not current_runner.browser_service:
            web_console.warning("截图请求失败: 浏览器服务不可用")
            return jsonify({
                'error': 'Browser service not available',
                'detail': 'BrowserService not created'
            }), 404

        if not current_runner.browser_service.is_initialized():
            web_console.warning("截图请求失败: 浏览器未初始化")
            return jsonify({
                'error': 'Browser not initialized',
                'detail': 'Browser initialization incomplete'
            }), 404

        # 获取截图
        web_console.info("📷 正在获取浏览器截图...")
        screenshot_bytes = current_runner.browser_service.take_screenshot_sync(full_page=False)

        if screenshot_bytes:
            web_console.info("✅ 截图获取成功")
            return Response(
                screenshot_bytes,
                mimetype='image/png',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Pragma': 'no-cache',
                    'Expires': '0',
                    'Content-Length': str(len(screenshot_bytes))
                }
            )
        else:
            web_console.error("截图获取失败: 返回数据为空")
            return jsonify({
                'error': 'Screenshot failed - no data returned',
                'detail': 'Browser may be busy or page not loaded'
            }), 500

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"截图API异常: {str(e)}"
        web_console.error(error_msg)
        web_console.error(f"错误详情: {error_details}")
        return jsonify({
            'error': f'Screenshot error: {str(e)}',
            'detail': 'Internal server error'
        }), 500
