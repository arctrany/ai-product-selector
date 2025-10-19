"""
Seerfar Web服务主程序 - 基于Flask的Web界面
提供表单输入和控制台界面，专注于场景相关的路由处理
业务逻辑已分离到 web_console_api 模块
"""

import os
from datetime import datetime
from typing import Dict, Any
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename

from web.web_console import web_console
from web.web_console_api import api_bp, set_form_data, register_task_executor
from playweight.utils.path_config import get_upload_dir

# 简化配置
app = Flask(__name__, template_folder='templates')
app.config['SECRET_KEY'] = 'seerfar-web-console-2024'
app.config['UPLOAD_FOLDER'] = get_upload_dir()  # 使用跨平台路径配置
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB

# 注册业务逻辑API蓝图
app.register_blueprint(api_bp)

# 注册Seerfar场景任务执行器
from playweight.scenes.web.seerfar_task_executor import SeerfarTaskExecutor
from web.web_console_api import register_task_executor

# 创建并注册Seerfar任务执行器
seerfar_executor = SeerfarTaskExecutor()
register_task_executor(seerfar_executor)
web_console.info("✅ Seerfar任务执行器已注册")

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

# ==================== 场景相关路由 ====================

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

        # 保存表单数据到API模块
        set_form_data(form_data)

        web_console.success("✅ 表单提交成功，跳转到控制台页面")
        return redirect(url_for('console_page'))

    except Exception as e:
        error_msg = f"表单处理失败: {str(e)}"
        web_console.error(error_msg)
        return jsonify({'success': False, 'error': error_msg}), 500

# ==================== 所有API路由已移至 web_console_api.py ====================
# 业务逻辑API包括：
# - /api/task/* (启动、暂停、恢复、停止任务)
# - /api/console/* (控制台状态、清空)
# - /api/browser/* (浏览器截图)

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