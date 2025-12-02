"""
ERP数据验证器配置文件

包含所有ERP数据验证所需的字段定义、正则表达式模式和其他配置项。
"""

# ERP必需字段标签（用户指定的核心字段）
REQUIRED_FIELD_LABELS = {
    'SKU', '重量', '尺寸', 'rFBS佣金'
}

# 尺寸相关的标签变体
DIMENSION_LABELS = {'尺寸', '长', '宽', '高', '长宽高'}

# 无效值标识符
INVALID_VALUES = {
    '-', '--', '无数据', 'N/A', '', '无', '暂无', 
    'null', 'undefined', '待更新', '加载中', '...'
}

# 必需字段的数据格式验证规则
VALIDATION_PATTERNS = {
    'sku': r'^\d+$',  # SKU应为纯数字
    'weight': r'^\d+(\.\d+)?(g|kg|克|公斤)?',  # 重量应为数字格式，可带单位
    'dimensions': r'\d+(\.\d+)?',  # 尺寸包含数字
    'rfbs_commission': r'\d+(\.\d+)?%?',  # rFBS佣金包含数字，可能有百分号
}

# 检查只有标签的模式
LABEL_ONLY_PATTERNS = [
    r'SKU：\s*重\s*量：',  # "SKU： 重量："
    r'重\s*量：\s*尺寸：',  # "重量： 尺寸："
    r'SKU：\s*长\s*[：:]\s*宽\s*[：:]',  # "SKU： 长： 宽："
    r'rFBS佣金：\s*重\s*量：',  # "rFBS佣金： 重量："
]

# 统计有效数据字段的模式
REQUIRED_FIELD_PATTERNS = {
    'sku': r'SKU：\s*(\d+)',  # SKU：1756017628
    'weight': r'重\s*量：\s*([0-9.]+(?:g|kg|克|公斤)?)',  # 重量：40g
    'dimensions': [  # 尺寸相关的多种模式
        r'尺寸：\s*([^：\n]+)',  # 尺寸：550 x 500 x 100mm
        r'长\s*[：:]\s*([0-9.]+)',  # 长：550
        r'宽\s*[：:]\s*([0-9.]+)',  # 宽：500
        r'高\s*[：:]\s*([0-9.]+)',  # 高：100
        r'([0-9.]+\s*[x×]\s*[0-9.]+\s*[x×]\s*[0-9.]+)',  # 550 x 500 x 100
    ],
    'rfbs_commission': r'rFBS佣金：\s*([0-9.,\s%]+)',  # rFBS佣金：8%
}

# 分析ERP数据时使用的字段模式
ANALYSIS_FIELD_PATTERNS = {
    'sku': r'SKU：\s*(\d+)',
    'weight': r'重\s*量：\s*([0-9.]+(?:g|kg|克|公斤)?)',
    'dimensions': r'(?:尺寸|长|宽|高)：\s*([^：\n]+)',
    'rfbs_commission': r'rFBS佣金：\s*([0-9.,\s%]+)',
}

# 验证数据格式的模式
REASONABLE_PATTERNS = [
    r'\d+',  # 包含数字
    r'[a-zA-Z\u4e00-\u9fa5]+/[a-zA-Z\u4e00-\u9fa5]+',  # 包含层级结构（如类目）
    r'[a-zA-Z\u4e00-\u9fa5]{2,}',  # 包含有意义的文字（非单字符）
]
