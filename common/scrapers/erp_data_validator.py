"""
ERP数据验证器

专门用于验证ERP插件数据的完整性和有效性，能够区分"只有标签的中间状态"和"有完整数据的最终状态"。
"""

import re
import logging
from typing import List, Dict, Any, Optional, Union
from bs4 import BeautifulSoup, Tag


class ErpDataValidator:
    """
    ERP数据验证器
    
    能够智能区分ERP数据的加载状态：
    - 中间状态：只有标签（如"类目：品牌：SKU："）
    - 完整状态：有实际数据值（如"类目：汽车用品/汽车内饰地垫"）
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初始化ERP数据验证器
        
        Args:
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # ERP关键字段标签（中文）
        self.erp_field_labels = {
            '类目', '品牌', 'SKU', '月销量', '月销售额', 
            '日销量', '日销售额', '价格', '重量', '尺寸',
            '上架时间', 'rFBS佣金', '佣金率'
        }
        
        # 无效值标识符
        self.invalid_values = {
            '-', '--', '无数据', 'N/A', '', '无', '暂无', 
            'null', 'undefined', '待更新', '加载中', '...'
        }
        
        # 数据格式验证规则
        self.validation_patterns = {
            'category': r'^[^：:]+/[^：:]+',  # 类目应包含层级结构，如"汽车用品/汽车内饰地垫"
            'sku': r'^\d+$',  # SKU应为纯数字
            'monthly_sales_volume': r'^\d+$',  # 月销量应为数字
            'monthly_sales_amount': r'^\d+',  # 月销售额应以数字开头
            'brand_name': r'^[^：:]+$',  # 品牌名不应包含冒号
            'price': r'^\d+(\.\d+)?',  # 价格应为数字格式
            'weight': r'^\d+(\.\d+)?',  # 重量应为数字格式
        }
    
    def validate_elements(self, elements: List[Union[Tag, str]]) -> bool:
        """
        验证ERP元素列表是否包含有效的完整数据
        
        Args:
            elements: BeautifulSoup元素列表
            
        Returns:
            bool: 是否包含有效的完整ERP数据
        """
        if not elements:
            self.logger.debug("❌ ERP验证失败：元素列表为空")
            return False
        
        try:
            # 提取所有文本内容进行分析
            all_text = self._extract_all_text(elements)
            
            if not all_text:
                self.logger.debug("❌ ERP验证失败：无法提取文本内容")
                return False
            
            self.logger.debug(f"🔍 ERP验证 - 提取的文本内容: {all_text[:200]}...")
            
            # 1. 检查是否只包含标签（中间状态）
            if self._is_only_labels(all_text):
                self.logger.debug("❌ ERP验证失败：只包含标签，数据未完全加载")
                return False
            
            # 2. 检查是否有有效的数据值
            valid_data_count = self._count_valid_data_fields(all_text)
            
            if valid_data_count < 2:  # 至少需要2个有效数据字段
                self.logger.debug(f"❌ ERP验证失败：有效数据字段数量不足 ({valid_data_count} < 2)")
                return False
            
            # 3. 验证数据格式的合理性
            if not self._validate_data_formats(all_text):
                self.logger.debug("❌ ERP验证失败：数据格式不符合预期")
                return False
            
            self.logger.debug(f"✅ ERP验证成功：发现 {valid_data_count} 个有效数据字段")
            return True
            
        except Exception as e:
            self.logger.warning(f"ERP验证过程出错: {e}")
            return False
    
    def _extract_all_text(self, elements: List[Union[Tag, str]]) -> str:
        """
        从元素列表中提取所有文本内容
        
        Args:
            elements: BeautifulSoup元素列表
            
        Returns:
            str: 合并的文本内容
        """
        all_texts = []
        
        for element in elements:
            try:
                if hasattr(element, 'get_text'):
                    text = element.get_text(strip=True)
                    if text:
                        all_texts.append(text)
                elif isinstance(element, str):
                    text = str(element).strip()
                    if text:
                        all_texts.append(text)
            except Exception as e:
                self.logger.debug(f"提取文本失败: {e}")
                continue
        
        return ' '.join(all_texts)
    
    def _is_only_labels(self, text: str) -> bool:
        """
        检查文本是否只包含标签（中间状态）
        
        Args:
            text: 要检查的文本
            
        Returns:
            bool: 是否只包含标签
        """
        # 统计标签和实际数据的比例
        label_count = 0
        data_value_count = 0
        
        # 按空格分割文本进行分析
        words = text.split()
        
        for word in words:
            # 检查是否为标签（以冒号结尾）
            if word.endswith('：') or word.endswith(':'):
                label_count += 1
            # 检查是否为有效的数据值
            elif self._is_valid_data_value(word):
                data_value_count += 1
        
        # 如果标签数量显著多于数据值数量，认为是中间状态
        if label_count >= 3 and data_value_count <= 1:
            return True
        
        # 检查是否包含典型的"只有标签"模式
        label_only_patterns = [
            r'类目：\s*品牌：',  # "类目： 品牌："
            r'SKU：\s*月销量：',  # "SKU： 月销量："
            r'品牌：\s*SKU：\s*月销量：',  # "品牌： SKU： 月销量："
        ]
        
        for pattern in label_only_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _count_valid_data_fields(self, text: str) -> int:
        """
        统计有效数据字段的数量
        
        Args:
            text: 要分析的文本
            
        Returns:
            int: 有效数据字段数量
        """
        valid_count = 0
        
        # 检查每个关键字段是否有有效数据
        field_patterns = {
            'category': r'类目：\s*([^：\s]+(?:/[^：\s]+)*)',  # 类目：汽车用品/汽车内饰地垫
            'brand_name': r'品牌：\s*([^：\s]+)',  # 品牌：COZYCAR
            'sku': r'SKU：\s*(\d+)',  # SKU：1756017628
            'monthly_sales_volume': r'月销量：\s*(\d+)',  # 月销量：123
            'monthly_sales_amount': r'月销售额：\s*([0-9,]+)',  # 月销售额：12,345
            'price': r'价格：\s*(\d+)',  # 价格：199
        }
        
        for field_name, pattern in field_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                # 验证匹配的值是否有效
                for match in matches:
                    if self._is_valid_data_value(match):
                        valid_count += 1
                        self.logger.debug(f"✅ 发现有效字段 {field_name}: {match}")
                        break  # 每个字段只计算一次
        
        return valid_count
    
    def _validate_data_formats(self, text: str) -> bool:
        """
        验证数据格式的合理性
        
        Args:
            text: 要验证的文本
            
        Returns:
            bool: 数据格式是否合理
        """
        # 如果文本过短，可能不是完整数据
        if len(text.strip()) < 30:
            return False
        
        # 检查是否包含合理的数据格式
        reasonable_patterns = [
            r'\d+',  # 包含数字
            r'[a-zA-Z\u4e00-\u9fa5]+/[a-zA-Z\u4e00-\u9fa5]+',  # 包含层级结构（如类目）
            r'[a-zA-Z\u4e00-\u9fa5]{2,}',  # 包含有意义的文字（非单字符）
        ]
        
        pattern_matches = 0
        for pattern in reasonable_patterns:
            if re.search(pattern, text):
                pattern_matches += 1
        
        # 至少匹配2个合理格式
        return pattern_matches >= 2
    
    def _is_valid_data_value(self, value: str) -> bool:
        """
        检查值是否为有效的数据值（非标签）
        
        Args:
            value: 要检查的值
            
        Returns:
            bool: 是否为有效数据值
        """
        if not value or not isinstance(value, str):
            return False
        
        value = value.strip()
        
        # 过滤无效值
        if value in self.invalid_values:
            return False
        
        # 过滤纯标签（以冒号结尾）
        if value.endswith('：') or value.endswith(':'):
            return False
        
        # 过滤过短的值（可能是不完整的数据）
        if len(value) < 2:
            return False
        
        # 有效的数据值应该包含实际内容
        return True
    
    def create_content_validator(self, min_valid_fields: int = 2) -> callable:
        """
        创建用于wait_for_content_smart的内容验证函数
        
        Args:
            min_valid_fields: 最少有效字段数量
            
        Returns:
            callable: 内容验证函数
        """
        def content_validator(elements: List[Union[Tag, str]]) -> bool:
            """
            ERP内容验证函数，用于wait_for_content_smart
            
            Args:
                elements: BeautifulSoup元素列表
                
            Returns:
                bool: 内容是否有效（ERP数据是否完全加载）
            """
            try:
                return self.validate_elements(elements)
            except Exception as e:
                self.logger.warning(f"ERP内容验证出错: {e}")
                return False
        
        return content_validator
    
    def analyze_erp_data(self, elements: List[Union[Tag, str]]) -> Dict[str, Any]:
        """
        分析ERP数据的详细信息（用于调试）
        
        Args:
            elements: BeautifulSoup元素列表
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        if not elements:
            return {'valid': False, 'reason': 'elements_empty', 'details': {}}
        
        try:
            all_text = self._extract_all_text(elements)
            
            analysis = {
                'valid': False,
                'text_length': len(all_text),
                'text_preview': all_text[:200] if all_text else '',
                'is_only_labels': self._is_only_labels(all_text),
                'valid_data_count': self._count_valid_data_fields(all_text),
                'format_valid': self._validate_data_formats(all_text),
                'details': {}
            }
            
            # 详细分析各个字段
            field_patterns = {
                'category': r'类目：\s*([^：\s]+(?:/[^：\s]+)*)',
                'brand_name': r'品牌：\s*([^：\s]+)',
                'sku': r'SKU：\s*(\d+)',
                'monthly_sales_volume': r'月销量：\s*(\d+)',
                'monthly_sales_amount': r'月销售额：\s*([0-9,]+)',
            }
            
            for field_name, pattern in field_patterns.items():
                matches = re.findall(pattern, all_text)
                analysis['details'][field_name] = {
                    'found': bool(matches),
                    'values': matches[:3] if matches else []  # 最多显示3个匹配值
                }
            
            # 综合判断
            analysis['valid'] = (
                not analysis['is_only_labels'] and
                analysis['valid_data_count'] >= 2 and
                analysis['format_valid']
            )
            
            return analysis
            
        except Exception as e:
            return {
                'valid': False,
                'reason': f'analysis_error: {e}',
                'details': {}
            }


# 全局实例管理
_erp_validator_instance = None

def get_erp_data_validator(logger: Optional[logging.Logger] = None) -> ErpDataValidator:
    """
    获取ERP数据验证器的全局实例
    
    Args:
        logger: 日志记录器
        
    Returns:
        ErpDataValidator: ERP数据验证器实例
    """
    global _erp_validator_instance
    
    if _erp_validator_instance is None:
        _erp_validator_instance = ErpDataValidator(logger=logger)
    
    return _erp_validator_instance
