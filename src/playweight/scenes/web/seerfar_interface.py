"""
Web用户界面模块 - 提供Web服务支持的用户交互功能
负责Web表单处理、配置管理和用户交互，支持智能选品系统
"""

import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, asdict

@dataclass
class FormField:
    """表单字段数据类"""
    type: str
    label: str
    variable_name: str
    value: Any = None
    required: bool = True

    # 文件字段特有属性
    filter: Optional[str] = None
    null_text: Optional[str] = None

    # 数值字段特有属性
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    use_float: bool = False


def _init_form_fields() -> List[FormField]:
    """初始化表单字段"""
    return [
        # 文件上传字段
        FormField(
            type="File",
            label="好店模版文件",
            variable_name="good_shop_file",
            filter="Excel文件|*.xls;*.xlsx",
            null_text="请选择路径"
        ),
        FormField(
            type="File",
            label="采品文件",
            variable_name="item_collect_file",
            filter="Excel文件|*.xls;*.xlsx",
            null_text="请选择商品"
        ),
        FormField(
            type="File",
            label="计算器文件",
            variable_name="margin_calculator",
            filter="Excel文件|*.xls;*.xlsx",
            null_text="请选择路径"
        ),

        # 数值输入字段
        FormField(
            type="Number",
            label="利润率大于等于",
            variable_name="margin",
            value=0.1,
            use_float=True
        ),
        FormField(
            type="Number",
            label="商品创建天数小于等于",
            variable_name="item_created_days",
            value=150,
            use_float=False
        ),
        FormField(
            type="Number",
            label="跟卖数量小于",
            variable_name="follow_buy_cnt",
            value=37,
            use_float=True
        ),
        FormField(
            type="Number",
            label="月销量大于等于",
            variable_name="max_monthly_sold",
            value=0,
            use_float=False
        ),
        FormField(
            type="Number",
            label="月销量小于等于",
            variable_name="monthly_sold_min",
            value=100,
            use_float=False
        ),
        FormField(
            type="Number",
            label="商品最小重量（g）",
            variable_name="item_min_weight",
            value=0,
            use_float=False
        ),
        FormField(
            type="Number",
            label="商品最大重量（g）",
            variable_name="item_max_weight",
            value=1000,
            use_float=False
        ),
        FormField(
            type="Number",
            label="G01商品最小售价（₽）",
            variable_name="g01_item_min_price",
            value=0,
            use_float=False
        ),
        FormField(
            type="Number",
            label="G01商品最大售价（₽）",
            variable_name="g01_item_max_price",
            value=1000,
            use_float=False
        )
    ]


class WebUserInterface:
    """Web用户界面类 - 处理Web表单和用户交互"""

    def __init__(self):
        """初始化Web用户界面"""
        # 系统配置
        self.config = {
            'request_delay': 2,
            'page_timeout': 30000,
            'max_retries': 3,
            'output_format': 'xlsx',
            'debug_mode': False,
            'web_port': 7788,
            'web_host': '127.0.0.1'
        }

        # 智能选品表单字段定义
        self.form_fields = _init_form_fields()

        # 用户设置存储
        self.user_settings = {}
        self.remember_settings = False

    def get_form_config(self) -> Dict[str, Any]:
        """获取表单配置"""
        return {
            "title": "智能选品",
            "fields": [asdict(field) for field in self.form_fields],
            "buttons": [
                {"label": "确定", "type": "submit", "theme": "primary"},
                {"label": "取消", "type": "button", "theme": "secondary"}
            ]
        }

    def validate_form_data(self, form_data: Dict[str, Any]) -> tuple[bool, List[str]]:
        """
        验证表单数据

        Args:
            form_data: 表单数据

        Returns:
            tuple[bool, List[str]]: (是否有效, 错误信息列表)
        """
        errors = []

        # 验证文件字段
        file_fields = [f for f in self.form_fields if f.type == "File"]
        for field in file_fields:
            value = form_data.get(field.variable_name)
            if field.required and (not value or not os.path.exists(value)):
                errors.append(f"{field.label}：请选择有效的文件路径")

        # 验证数值字段
        number_fields = [f for f in self.form_fields if f.type == "Number"]
        for field in number_fields:
            value = form_data.get(field.variable_name)
            if value is not None:
                try:
                    if field.use_float:
                        num_value = float(value)
                    else:
                        num_value = int(value)

                    if field.min_value is not None and num_value < field.min_value:
                        errors.append(f"{field.label}：值不能小于 {field.min_value}")

                    if field.max_value is not None and num_value > field.max_value:
                        errors.append(f"{field.label}：值不能大于 {field.max_value}")

                except (ValueError, TypeError):
                    errors.append(f"{field.label}：请输入有效的数值")

        return len(errors) == 0, errors

    def process_form_submission(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理表单提交

        Args:
            form_data: 表单数据

        Returns:
            Dict[str, Any]: 处理后的配置数据
        """
        # 验证数据
        is_valid, errors = self.validate_form_data(form_data)
        if not is_valid:
            raise ValueError(f"表单验证失败: {'; '.join(errors)}")

        # 处理记住设置选项
        self.remember_settings = form_data.get('remember_settings', False)

        # 转换数据类型
        processed_data = {}
        for field in self.form_fields:
            value = form_data.get(field.variable_name)
            if value is not None:
                if field.type == "Number":
                    if field.use_float:
                        processed_data[field.variable_name] = float(value)
                    else:
                        processed_data[field.variable_name] = int(value)
                else:
                    processed_data[field.variable_name] = value

        # 保存用户设置（如果选择记住）
        if self.remember_settings:
            self.save_user_settings(processed_data)

        return processed_data

    def save_user_settings(self, settings: Dict[str, Any]):
        """保存用户设置到本地文件"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), 'user_settings.json')
            with open(settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            self.user_settings = settings.copy()
        except Exception as e:
            print(f"保存用户设置失败: {e}")

    def load_user_settings(self) -> Dict[str, Any]:
        """从本地文件加载用户设置"""
        try:
            settings_file = os.path.join(os.path.dirname(__file__), 'user_settings.json')
            if os.path.exists(settings_file):
                with open(settings_file, 'r', encoding='utf-8') as f:
                    self.user_settings = json.load(f)
                    return self.user_settings.copy()
        except Exception as e:
            print(f"加载用户设置失败: {e}")

        return {}

    def get_field_default_value(self, variable_name: str) -> Any:
        """获取字段的默认值（考虑用户设置）"""
        # 优先使用用户保存的设置
        if variable_name in self.user_settings:
            return self.user_settings[variable_name]

        # 使用字段定义的默认值
        for field in self.form_fields:
            if field.variable_name == variable_name:
                return field.value

        return None

    def get_config(self, key: str = None) -> Any:
        """获取系统配置"""
        if key is None:
            return self.config.copy()
        return self.config.get(key)

    def set_config(self, key: str, value: Any) -> bool:
        """设置系统配置"""
        if key in self.config:
            self.config[key] = value
            return True
        return False

    def get_web_url(self, path: str = "") -> str:
        """获取Web服务URL"""
        host = self.config['web_host']
        port = self.config['web_port']
        return f"http://{host}:{port}{path}"

    def format_task_config(self, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        格式化任务配置，用于传递给执行引擎

        Args:
            form_data: 表单数据

        Returns:
            Dict[str, Any]: 格式化后的任务配置
        """
        return {
            'files': {
                'good_shop_file': form_data.get('good_shop_file'),
                'item_collect_file': form_data.get('item_collect_file'),
                'margin_calculator': form_data.get('margin_calculator')
            },
            'parameters': {
                'margin': form_data.get('margin', 0.1),
                'item_created_days': form_data.get('item_created_days', 150),
                'follow_buy_cnt': form_data.get('follow_buy_cnt', 37),
                'max_monthly_sold': form_data.get('max_monthly_sold', 0),
                'monthly_sold_min': form_data.get('monthly_sold_min', 100),
                'item_min_weight': form_data.get('item_min_weight', 0),
                'item_max_weight': form_data.get('item_max_weight', 1000),
                'g01_item_min_price': form_data.get('g01_item_min_price', 0),
                'g01_item_max_price': form_data.get('g01_item_max_price', 1000)
            },
            'system': self.config.copy(),
            'timestamp': datetime.now().isoformat()
        }

# 向后兼容的别名
UserInterface = WebUserInterface