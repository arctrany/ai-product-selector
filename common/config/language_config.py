"""
多语言配置管理
支持动态语言切换，消除硬编码的语言相关文本
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
import os


class SupportedLanguage(Enum):
    """支持的语言"""
    CHINESE = "zh"
    RUSSIAN = "ru" 
    ENGLISH = "en"


@dataclass
class LanguageConfig:
    """语言配置类"""
    
    # 当前语言设置
    current_language: SupportedLanguage = SupportedLanguage.RUSSIAN
    
    # 回退语言（当前语言不可用时使用）
    fallback_language: SupportedLanguage = SupportedLanguage.ENGLISH
    
    # 跟卖检测关键词（多语言）
    competitor_keywords: Dict[str, List[str]] = field(default_factory=lambda: {
        "zh": [
            "有其他卖家销售",
            "跟卖", 
            "其他卖家",
            "更多卖家",
            "其他店铺"
        ],
        "ru": [
            "Продают другие продавцы",
            "Другие продавцы",
            "Еще продавцы", 
            "Другие магазины",
            "продавца",
            "Есть быстрее"
        ],
        "en": [
            "Other sellers",
            "More sellers",
            "Additional sellers",
            "Other stores",
            "sellers"
        ]
    })
    
    # 跟卖数量解析模式（多语言正则表达式）
    competitor_count_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        "zh": [
            r'(\d+)\s*卖家',
            r'(\d+)\s*店铺', 
            r'共\s*(\d+)',
            r'总计\s*(\d+)',
            r'(\d+)\s*个卖家',
            r'(\d+)\s*家店铺'
        ],
        "ru": [
            r'(\d+)\s*продавца',
            r'(\d+)\s*продавцов',
            r'(\d+)\s*магазина',
            r'(\d+)\s*магазинов',
            r'Всего\s*(\d+)',
            r'(\d+)\s*других'
        ],
        "en": [
            r'(\d+)\s*sellers?',
            r'(\d+)\s*stores?',
            r'Total\s*(\d+)', 
            r'(\d+)\s*other',
            r'(\d+)\s*additional',
            r'(\d+)\s*more'
        ]
    })
    
    # 排除文本模式（用于过滤标题等非有效内容）
    exclude_text_patterns: Dict[str, List[str]] = field(default_factory=lambda: {
        "zh": [
            "其他卖家", 
            "更多卖家",
            "卖家列表",
            "商家信息"
        ],
        "ru": [
            "других продавцов",
            "другие продавцы", 
            "список продавцов",
            "информация о продавцах"
        ],
        "en": [
            "other sellers",
            "more sellers",
            "seller list", 
            "seller information"
        ]
    })
    
    # 展开按钮文本模式
    expand_button_texts: Dict[str, List[str]] = field(default_factory=lambda: {
        "zh": [
            "显示",
            "展开", 
            "查看更多",
            "显示全部",
            "更多"
        ],
        "ru": [
            "показать",
            "развернуть",
            "показать больше", 
            "показать все",
            "еще"
        ],
        "en": [
            "show",
            "expand",
            "show more",
            "show all", 
            "more"
        ]
    })
    
    # 数据单位识别模式
    unit_patterns: Dict[str, Dict[str, List[str]]] = field(default_factory=lambda: {
        "weight": {
            "zh": [r'([0-9.]+)\s*(克|公斤|千克|g|kg)', r'重量[：:]\s*([0-9.]+)\s*(克|公斤|千克|g|kg)'],
            "ru": [r'([0-9.]+)\s*(г|кг|грамм|килограмм)', r'Вес[：:]\s*([0-9.]+)\s*(г|кг|грамм|килограмм)'],
            "en": [r'([0-9.]+)\s*(g|kg|gram|kilogram)', r'Weight[：:]\s*([0-9.]+)\s*(g|kg|gram|kilogram)']
        },
        "volume": {
            "zh": [r'([0-9.]+)\s*(毫升|升|ml|l)', r'容量[：:]\s*([0-9.]+)\s*(毫升|升|ml|l)'],
            "ru": [r'([0-9.]+)\s*(мл|л|миллилитр|литр)', r'Объем[：:]\s*([0-9.]+)\s*(мл|л|миллилитр|литр)'],
            "en": [r'([0-9.]+)\s*(ml|l|milliliter|liter)', r'Volume[：:]\s*([0-9.]+)\s*(ml|l|milliliter|liter)']
        }
    })
    
    def get_competitor_keywords(self, language: Optional[SupportedLanguage] = None) -> List[str]:
        """获取跟卖检测关键词"""
        lang = language or self.current_language
        keywords = self.competitor_keywords.get(lang.value, [])
        
        # 如果当前语言没有关键词，使用回退语言
        if not keywords and lang != self.fallback_language:
            keywords = self.competitor_keywords.get(self.fallback_language.value, [])
            
        return keywords
    
    def get_competitor_count_patterns(self, language: Optional[SupportedLanguage] = None) -> List[str]:
        """获取跟卖数量解析模式"""
        lang = language or self.current_language
        patterns = self.competitor_count_patterns.get(lang.value, [])
        
        # 如果当前语言没有模式，使用回退语言
        if not patterns and lang != self.fallback_language:
            patterns = self.competitor_count_patterns.get(self.fallback_language.value, [])
            
        return patterns
    
    def get_exclude_text_patterns(self, language: Optional[SupportedLanguage] = None) -> List[str]:
        """获取排除文本模式"""
        lang = language or self.current_language
        patterns = self.exclude_text_patterns.get(lang.value, [])
        
        # 如果当前语言没有模式，使用回退语言
        if not patterns and lang != self.fallback_language:
            patterns = self.exclude_text_patterns.get(self.fallback_language.value, [])
            
        return patterns
    
    def get_expand_button_texts(self, language: Optional[SupportedLanguage] = None) -> List[str]:
        """获取展开按钮文本"""
        lang = language or self.current_language
        texts = self.expand_button_texts.get(lang.value, [])
        
        # 如果当前语言没有文本，使用回退语言
        if not texts and lang != self.fallback_language:
            texts = self.expand_button_texts.get(self.fallback_language.value, [])
            
        return texts
    
    def get_unit_patterns(self, unit_type: str, language: Optional[SupportedLanguage] = None) -> List[str]:
        """获取数据单位识别模式"""
        lang = language or self.current_language
        patterns = self.unit_patterns.get(unit_type, {}).get(lang.value, [])
        
        # 如果当前语言没有模式，使用回退语言
        if not patterns and lang != self.fallback_language:
            patterns = self.unit_patterns.get(unit_type, {}).get(self.fallback_language.value, [])
            
        return patterns
    
    def is_exclude_text(self, text: str, language: Optional[SupportedLanguage] = None) -> bool:
        """检查文本是否应该被排除"""
        if not text:
            return False
            
        exclude_patterns = self.get_exclude_text_patterns(language)
        text_lower = text.lower()
        
        for pattern in exclude_patterns:
            if pattern.lower() in text_lower:
                return True
                
        return False
    
    def detect_language_from_text(self, text: str) -> Optional[SupportedLanguage]:
        """从文本中检测语言"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        # 检测俄语
        ru_chars = set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')
        if any(char in ru_chars for char in text_lower):
            return SupportedLanguage.RUSSIAN
            
        # 检测中文
        for char in text:
            if '\u4e00' <= char <= '\u9fff':
                return SupportedLanguage.CHINESE
                
        # 默认为英语
        return SupportedLanguage.ENGLISH
    
    def set_language_from_environment(self):
        """从环境变量设置语言"""
        env_lang = os.getenv('OZON_SCRAPER_LANGUAGE', '').lower()
        
        if env_lang in ['zh', 'chinese', '中文']:
            self.current_language = SupportedLanguage.CHINESE
        elif env_lang in ['ru', 'russian', 'русский']:
            self.current_language = SupportedLanguage.RUSSIAN  
        elif env_lang in ['en', 'english', 'английский']:
            self.current_language = SupportedLanguage.ENGLISH
    
    def get_all_supported_languages(self) -> List[SupportedLanguage]:
        """获取所有支持的语言"""
        return list(SupportedLanguage)


# 全局默认语言配置实例
DEFAULT_LANGUAGE_CONFIG = LanguageConfig()

def get_language_config() -> LanguageConfig:
    """获取语言配置实例"""
    # 尝试从环境变量设置语言
    DEFAULT_LANGUAGE_CONFIG.set_language_from_environment()
    return DEFAULT_LANGUAGE_CONFIG

def set_current_language(language: SupportedLanguage):
    """设置当前语言"""
    DEFAULT_LANGUAGE_CONFIG.current_language = language

def get_current_language() -> SupportedLanguage:
    """获取当前语言"""
    return DEFAULT_LANGUAGE_CONFIG.current_language
