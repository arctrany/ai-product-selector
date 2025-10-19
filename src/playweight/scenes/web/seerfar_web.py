"""
Seerfar Web服务主程序 - 基于Flask的Web界面
提供表单输入和控制台界面，支持实时任务控制和输出
"""

import os
import json
import asyncio
import threading
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from werkzeug.utils import secure_filename

from web.web_console import web_console
from playweight.utils.path_config import get_upload_dir

# 简化配置
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'seerfar-web-console-2024'
app.config['UPLOAD_FOLDER'] = get_upload_dir()  # 使用跨平台路径配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 上传目录已通过 get_upload_dir() 自动创建

# 全局变量
current_task_thread = None
current_form_data = None
task_stop_flag = False  # 添加停止标志
current_runner = None  # 添加当前Runner实例的引用


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'xls', 'xlsx'}


def save_uploaded_file(file, field_name):
    """保存上传的文件"""
    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        web_console.info(f"文件已保存: {field_name} -> {filename}")
        return filepath
    return None


async def run_automation_task(task_id: str, form_data: Dict[str, Any]):
    """运行自动化任务 - 直接使用真实的业务逻辑"""
    global task_stop_flag
    task_stop_flag = False  # 重置停止标志

    try:
        web_console.info(f"开始执行自动化任务: {task_id}")

        # 导入真实的业务逻辑组件
        from playweight.scenes.automation_scenario import AutomationScenario
        from playweight.runner import Runner
        import pandas as pd

        web_console.info("✅ 核心模块导入成功")

        # 获取好店模版文件路径
        excel_file_path = form_data.get('good_shop_file')
        if not excel_file_path or not os.path.exists(excel_file_path):
            error_msg = "好店模版文件不存在"
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        # 读取Excel文件获取店铺数据
        web_console.update_progress(task_id, 10, "读取好店模版文件...")
        try:
            df = pd.read_excel(excel_file_path)
            stores_data = df.to_dict('records')
            web_console.info(f"✅ 成功读取 {len(stores_data)} 个店铺数据")
        except Exception as e:
            error_msg = f"Excel文件读取失败: {str(e)}"
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        # 初始化浏览器环境
        web_console.update_progress(task_id, 20, "初始化浏览器环境...")
        runner = Runner()

        # 保存Runner实例的全局引用，用于截图API
        global current_runner
        current_runner = runner

        if not await runner.initialize_system():
            error_msg = "浏览器环境初始化失败"
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        web_console.info("✅ 浏览器环境初始化完成")

        # 创建自动化场景实例
        web_console.update_progress(task_id, 30, "创建自动化场景...")

        # 从用户配置获取参数，提供默认值
        max_products_per_store = form_data.get('max_products_per_store', 50)

        automation_scenario = AutomationScenario(
            request_delay=2.0,
            debug_mode=True,
            max_products_per_store=max_products_per_store
        )

        # 设置页面对象到自动化场景
        runner.set_scenario(automation_scenario)
        web_console.info("✅ 自动化场景创建成功")

        # 关键步骤：设置用户界面，这会创建页面对象并设置到场景中
        web_console.update_progress(task_id, 35, "设置用户界面和页面对象...")
        print("🔧 正在设置用户界面和页面对象...")
        web_console.info("🔧 正在设置用户界面和页面对象...")

        if not runner.setup_user_interface():
            error_msg = "用户界面设置失败 - 页面对象创建失败"
            print(f"❌ {error_msg}")
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        print("✅ 用户界面和页面对象设置完成")
        web_console.info("✅ 用户界面和页面对象设置完成")

        # 执行店铺爬取
        web_console.update_progress(task_id, 40, f"开始爬取 {len(stores_data)} 个店铺...")
        print(f"🚀 开始执行店铺爬取，共 {len(stores_data)} 个店铺")
        web_console.info(f"🚀 开始执行店铺爬取，共 {len(stores_data)} 个店铺")

        # 详细日志：显示店铺信息
        for i, store in enumerate(stores_data, 1):
            # 尝试多种可能的店铺ID字段名
            store_id = (store.get('store_id') or
                        store.get('店铺ID') or
                        store.get('店铺id') or
                        store.get('shop_id') or
                        store.get('shopId') or
                        store.get('id') or
                        store.get('ID') or
                        f"店铺{i}")
            print(f"📋 店铺 {i}: ID={store_id}")
            web_console.info(f"📋 店铺 {i}: ID={store_id}")

        # 检查停止标志
        if task_stop_flag or web_console.should_stop():
            web_console.warning("⚠️ 任务被用户停止")
            web_console.complete_task(task_id)
            return

        # 创建一个包装函数来检查停止状态
        async def crawl_with_stop_check():
            """带停止检查的爬取函数"""
            try:
                # 将停止检查函数传递给自动化场景
                if hasattr(automation_scenario, 'set_stop_callback'):
                    automation_scenario.set_stop_callback(lambda: task_stop_flag or web_console.should_stop())

                # 执行爬取，逐个店铺处理以便及时响应停止信号
                results = []

                for i, store in enumerate(stores_data):
                    # 检查停止信号 - 每个店铺处理前都检查
                    if task_stop_flag or web_console.should_stop():
                        web_console.warning("⚠️ 任务在执行过程中被用户停止")
                        break

                    # 更新进度
                    progress = 40 + (i / len(stores_data)) * 40
                    web_console.update_progress(task_id, progress, f"正在处理第 {i+1}/{len(stores_data)} 个店铺...")

                    # 逐个处理店铺，这样可以更及时地响应停止信号
                    try:
                        store_results = await automation_scenario.crawl_all_stores([store], limit=None)
                        if store_results:
                            results.extend(store_results)
                    except Exception as e:
                        web_console.warning(f"店铺 {i+1} 处理失败: {str(e)}")
                        continue

                    # 短暂延迟，给停止信号检查机会
                    await asyncio.sleep(0.1)

                return results

            except Exception as e:
                web_console.error(f"爬取过程中出现异常: {str(e)}")
                raise

        results = await crawl_with_stop_check()

        if not results:
            error_msg = "没有成功爬取任何店铺数据"
            web_console.error(error_msg)
            web_console.set_task_error(task_id, error_msg)
            return

        # 统计成功的结果
        successful_results = [r for r in results if r.get('success', False)]
        total_products = sum(len(r.get('products', [])) for r in successful_results)

        web_console.update_progress(task_id, 80, f"爬取完成，成功 {len(successful_results)} 个店铺")

        # 保存结果
        web_console.update_progress(task_id, 90, "保存结果...")
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 从用户配置获取输出格式，默认为xlsx
        output_format = form_data.get('output_format', 'xlsx')

        # 根据格式确定文件扩展名和保存方法
        if output_format == 'csv':
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"智能选品结果_{timestamp}.csv")
        elif output_format == 'json':
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"智能选品结果_{timestamp}.json")
        else:  # 默认xlsx
            output_file = os.path.join(app.config['UPLOAD_FOLDER'], f"智能选品结果_{timestamp}.xlsx")

        try:
            # 将结果转换为统一格式
            all_products = []
            for result in successful_results:
                products = result.get('products', [])
                for product in products:
                    product['store_id'] = result.get('store_id', '')
                    product['extraction_time'] = result.get('extraction_time', '')
                    all_products.append(product)

            if all_products:
                if output_format == 'csv':
                    df_results = pd.DataFrame(all_products)
                    df_results.to_csv(output_file, index=False, encoding='utf-8-sig')
                elif output_format == 'json':
                    import json
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump(all_products, f, ensure_ascii=False, indent=2)
                else:  # xlsx
                    df_results = pd.DataFrame(all_products)
                    df_results.to_excel(output_file, index=False)

                web_console.info(f"✅ 结果已保存到: {output_file} (格式: {output_format.upper()})")
            else:
                web_console.warning("⚠️ 没有商品数据可保存")
        except Exception as e:
            web_console.warning(f"⚠️ 结果保存失败: {str(e)}")

        # 清理浏览器资源
        try:
            await runner.cleanup_system()
        except Exception as e:
            web_console.warning(f"浏览器清理时出现警告: {str(e)}")

        # 清理全局Runner引用
        current_runner = None

        web_console.update_progress(task_id, 100, "任务完成")
        web_console.success("🎉 智能选品自动化任务执行完成！")

        # 显示真实的执行结果
        web_console.info("📈 任务执行结果:")
        web_console.info(f"  - 处理的好店模版: {os.path.basename(excel_file_path)}")
        web_console.info(f"  - 总店铺数量: {len(stores_data)}")
        web_console.info(f"  - 成功处理: {len(successful_results)}")
        web_console.info(f"  - 成功率: {len(successful_results) / len(stores_data) * 100:.1f}%")
        web_console.info(f"  - 总商品数量: {total_products}")

        web_console.complete_task(task_id)

    except Exception as e:
        error_msg = f"任务执行失败: {str(e)}"
        web_console.error(error_msg)
        import traceback
        web_console.error(f"错误堆栈: {traceback.format_exc()}")
        web_console.set_task_error(task_id, error_msg)

        # 出错时也要清理全局Runner引用
        current_runner = None


@app.route('/')
def index():
    """主页 - 重定向到表单页面"""
    return redirect(url_for('form_page'))


@app.route('/app')
@app.route('/app/<scene_id>')
def form_page(scene_id=None):
    """表单页面 - 智能选品配置"""
    web_console.info(f"用户访问表单页面, scene_id: {scene_id or 'default'}")
    return render_template('seerfar_form.html', scene_id=scene_id)


@app.route('/console')
def console_page():
    """控制台页面"""
    web_console.info("用户访问控制台页面")
    return render_template('console.html')


@app.route('/submit', methods=['POST'])
def submit_form():
    """处理表单提交"""
    try:
        web_console.info("收到表单提交请求")
        form_data = {}

        # 处理文件字段
        file_fields = ['good_shop_file', 'item_collect_file', 'margin_calculator']
        for field in file_fields:
            if field in request.files:
                file = request.files[field]
                if file and file.filename:
                    filepath = save_uploaded_file(file, field)
                    if filepath:
                        form_data[field] = filepath

        # 处理数值字段
        number_fields = [
            'margin', 'item_created_days', 'follow_buy_cnt',
            'max_monthly_sold', 'monthly_sold_min', 'item_min_weight',
            'item_max_weight', 'g01_item_min_price', 'g01_item_max_price',
            'max_products_per_store'
        ]

        for field in number_fields:
            value = request.form.get(field)
            if value:
                try:
                    if field == 'margin':
                        form_data[field] = float(value)
                    elif field == 'max_products_per_store':
                        form_data[field] = max(1, min(200, int(value)))  # 限制范围1-200
                    else:
                        form_data[field] = int(value) if '.' not in value else float(value)
                except ValueError:
                    web_console.warning(f"无效的数值字段: {field} = {value}")

        # 处理选择字段
        select_fields = ['output_format']
        for field in select_fields:
            value = request.form.get(field)
            if value:
                form_data[field] = value

        # 处理复选框
        form_data['remember_settings'] = 'remember_settings' in request.form

        # 验证必需字段
        if 'good_shop_file' not in form_data:
            web_console.error("缺少必需的好店模版文件")
            return jsonify({'success': False, 'error': '请选择好店模版文件'}), 400

        # 保存表单数据到全局变量
        global current_form_data
        current_form_data = form_data.copy()

        web_console.success("✅ 表单提交成功，跳转到控制台页面")
        return redirect(url_for('console_page'))

    except Exception as e:
        error_msg = f"表单处理失败: {str(e)}"
        web_console.error(error_msg)
        return jsonify({'success': False, 'error': error_msg}), 500


@app.route('/api/task/start', methods=['POST'])
def start_task():
    """启动任务API"""
    global current_task_thread

    try:
        if web_console.is_task_running():
            return jsonify({'success': False, 'error': '任务已在运行中'}), 400

        task_id = f"task_{uuid.uuid4().hex[:8]}"
        task = web_console.create_task(task_id, "智能选品自动化任务", total_items=10)

        if current_form_data is None:
            return jsonify({'success': False, 'error': '没有找到表单数据，请先填写并提交表单'}), 400

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


@app.route('/api/task/<task_id>/pause', methods=['POST'])
def pause_task(task_id):
    """暂停任务API"""
    try:
        web_console.pause_task(task_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/task/<task_id>/resume', methods=['POST'])
def resume_task(task_id):
    """恢复任务API"""
    try:
        web_console.resume_task(task_id)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/task/<task_id>/stop', methods=['POST'])
def stop_task(task_id):
    """停止任务API"""
    global task_stop_flag, current_task_thread
    try:
        task_stop_flag = True  # 设置停止标志
        web_console.stop_task(task_id)
        web_console.warning("🛑 用户请求停止任务")

        # 如果线程还在运行，等待一段时间让它自然结束
        if current_task_thread and current_task_thread.is_alive():
            web_console.info("等待任务线程结束...")

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/console/state')
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


@app.route('/api/console/clear', methods=['POST'])
def clear_console():
    """清空控制台API"""
    try:
        web_console.clear_messages()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/browser/screenshot', methods=['GET'])
def get_browser_screenshot():
    """获取浏览器截图API - 实现类似视频的体验"""
    try:
        global current_runner

        # 详细的状态检查和错误报告
        if not current_runner:
            web_console.warning("截图请求失败: 没有活跃的浏览器会话")
            return jsonify({'error': 'No active browser session', 'detail': 'Task not started or browser not initialized'}), 404

        if not hasattr(current_runner, 'browser_service') or not current_runner.browser_service:
            web_console.warning("截图请求失败: 浏览器服务不可用")
            return jsonify({'error': 'Browser service not available', 'detail': 'BrowserService not created'}), 404

        if not current_runner.browser_service.is_initialized():
            web_console.warning("截图请求失败: 浏览器未初始化")
            return jsonify({'error': 'Browser not initialized', 'detail': 'Browser initialization incomplete'}), 404

        # 使用BrowserService的同步截图方法，避免事件循环冲突
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
            return jsonify({'error': 'Screenshot failed - no data returned', 'detail': 'Browser may be busy or page not loaded'}), 500

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        error_msg = f"截图API异常: {str(e)}"
        web_console.error(error_msg)
        web_console.error(f"错误详情: {error_details}")
        return jsonify({'error': f'Screenshot error: {str(e)}', 'detail': 'Internal server error'}), 500


def run_web_server(host='127.0.0.1', port=7788, debug=False):
    """运行Web服务器"""
    web_console.info(f"🚀 启动Seerfar Web服务")
    web_console.info(f"📍 访问地址: http://{host}:{port}")
    web_console.info(f"📋 表单页面: http://{host}:{port}/app")
    web_console.info(f"🖥️ 控制台页面: http://{host}:{port}/console")

    try:
        app.run(host=host, port=port, debug=debug, threaded=True)
    except Exception as e:
        web_console.error(f"Web服务器启动失败: {str(e)}")
        raise


if __name__ == "__main__":
    """程序入口点 - 直接启动Web服务"""
    run_web_server()
