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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, logger: Optional[logging.Logger] = None):
        """
        初始化ERP数据验证器

        Args:
            config: 字段配置字典（从scraper获取），包含所有字段定义
            logger: 日志记录器
        """
        self.logger = logger or logging.getLogger(__name__)

        # 使用传入的配置或默认配置
        if config is None:
            config = self._get_default_config()

        # 从配置中获取字段定义
        self.required_field_labels = config.get('required_field_labels', {'SKU', '重量', '尺寸', 'rFBS佣金'})
        self.dimension_labels = config.get('dimension_labels', {'尺寸', '长', '宽', '高', '长宽高'})
        self.invalid_values = config.get('invalid_values', {'-', '--', '无数据', 'N/A', '', '无', '暂无', 'null', 'undefined'})
        self.validation_patterns = config.get('validation_patterns', {})
        self.label_only_patterns = config.get('label_only_patterns', [])
        self.required_field_patterns = config.get('required_field_patterns', {})
        self.reasonable_patterns = config.get('reasonable_patterns', [r'\d+', r'[a-zA-Z\u4e00-\u9fa5]+/[a-zA-Z\u4e00-\u9fa5]+', r'[a-zA-Z\u4e00-\u9fa5]{2,}'])
        self.analysis_field_patterns = config.get('analysis_field_patterns', self.required_field_patterns)

    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取默认配置（用于向后兼容）

        Returns:
            Dict[str, Any]: 默认配置字典
        """
        return {
            'required_field_labels': {'SKU', '重量', '尺寸', 'rFBS佣金'},
            'dimension_labels': {'尺寸', '长', '宽', '高', '长宽高'},
            'invalid_values': {'-', '--', '无数据', 'N/A', '', '无', '暂无', 'null', 'undefined'},
            'validation_patterns': {
                'sku': r'^\d+$',
                'weight': r'^\d+(\.\d+)?(g|kg|克|公斤)?',
                'dimensions': r'\d+(\.\d+)?',
                'rfbs_commission': r'\d+(\.\d+)?%?',
            },
            'label_only_patterns': [
                r'SKU：\s*重\s*量：',
                r'重\s*量：\s*尺寸：',
                r'SKU：\s*长\s*[：:]\s*宽\s*[：:]',
                r'rFBS佣金：\s*重\s*量：',
            ],
            'required_field_patterns': {
                'sku': r'SKU：\s*(\d+)',
                'weight': r'重\s*量：\s*([0-9.]+(?:g|kg|克|公斤)?)',
                'dimensions': [
                    r'尺寸：\s*([^：\n]+)',
                    r'长\s*[：:]\s*([0-9.]+)',
                    r'宽\s*[：:]\s*([0-9.]+)',
                    r'高\s*[：:]\s*([0-9.]+)',
                    r'([0-9.]+\s*[x×]\s*[0-9.]+\s*[x×]\s*[0-9.]+)',
                ],
                'rfbs_commission': r'rFBS佣金：\s*([0-9.,\s%]+)',
            }
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
            
            if valid_data_count < 1:  # 修复商品ID 1176594312问题：降低验证要求至少1个有效数据字段
                self.logger.debug(f"❌ ERP验证失败：有效数据字段数量不足 ({valid_data_count} < 1)")
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
        
        # 检查是否包含典型的"只有必需字段标签"模式
        for pattern in self.label_only_patterns:
            if re.search(pattern, text):
                return True
        
        return False
    
    def _count_valid_data_fields(self, text: str) -> int:
        """
        统计必需字段的有效数据数量

        Args:
            text: 要分析的文本

        Returns:
            int: 有效的必需字段数量
        """
        valid_count = 0

        # 检查每个必需字段是否有有效数据
        for field_name, patterns in self.required_field_patterns.items():
            field_found = False

            # 处理尺寸字段的多种模式
            if field_name == 'dimensions':
                for pattern in patterns:
                    matches = re.findall(pattern, text, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if self._is_valid_data_value(match):
                                valid_count += 1
                                field_found = True
                                self.logger.debug(f"✅ 发现有效字段 {field_name}: {match}")
                                break
                        if field_found:
                            break
            else:
                # 处理其他字段
                if isinstance(patterns, str):
                    matches = re.findall(patterns, text, re.IGNORECASE)
                    if matches:
                        for match in matches:
                            if self._is_valid_data_value(match):
                                valid_count += 1
                                field_found = True
                                self.logger.debug(f"✅ 发现有效字段 {field_name}: {match}")
                                break
        
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
        pattern_matches = 0
        for pattern in self.reasonable_patterns:
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
            
            # 详细分析必需字段
            field_patterns = self.analysis_field_patterns
            
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

def get_erp_data_validator(logger: Optional[logging.Logger] = None, scraper_instance: Optional[Any] = None) -> ErpDataValidator:
    """
    获取ERP数据验证器实例

    Args:
        logger: 日志记录器
        scraper_instance: ErpPluginScraper实例，用于获取字段配置

    Returns:
        ErpDataValidator: ERP数据验证器实例
    """
    # 如果提供了scraper实例，从中获取配置并创建新实例
    if scraper_instance and hasattr(scraper_instance, 'get_required_fields_config'):
        config = scraper_instance.get_required_fields_config()
        return ErpDataValidator(config=config, logger=logger)

    # 否则使用全局实例（向后兼容）
    global _erp_validator_instance
    
    if _erp_validator_instance is None:
        _erp_validator_instance = ErpDataValidator(logger=logger)
    
    return _erp_validator_instance
