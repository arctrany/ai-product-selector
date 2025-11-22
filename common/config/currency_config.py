"""
货币符号配置

统一管理项目中使用的所有货币符号，避免硬编码。
支持多种货币格式和本地化显示。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import os


@dataclass
class CurrencyConfig:
    """货币符号配置类"""
    
    # 支持的货币符号映射
    symbols: Dict[str, str] = field(default_factory=lambda: {
        'ruble': '₽',
        'ruble_text': 'руб',
        'ruble_en': 'rub',
        'ruble_en_upper': 'RUB',
        'yuan': '¥',
        'yuan_text': 'yuan',
        'yuan_code': 'CNY',
        'dollar': '$',
        'dollar_code': 'USD',
        'euro': '€',
        'euro_code': 'EUR'
    })
    
    # 货币符号列表（用于搜索和识别）
    currency_symbols: List[str] = field(default_factory=lambda: [
        '₽', 'руб', 'rub', 'RUB',
        '¥', 'yuan', 'CNY',
        '$', 'USD',
        '€', 'EUR'
    ])
    
    # 默认货币（项目主要使用的货币）
    default_currency: str = 'ruble'
    
    # 汇率配置（可从环境变量覆盖）
    exchange_rates: Dict[str, float] = field(default_factory=lambda: {
        'rub_to_cny': float(os.getenv('RUB_TO_CNY_RATE', '0.11')),
        'usd_to_cny': float(os.getenv('USD_TO_CNY_RATE', '7.0')),
        'eur_to_cny': float(os.getenv('EUR_TO_CNY_RATE', '7.5'))
    })
    
    def get_symbol(self, currency_key: str) -> str:
        """获取货币符号"""
        return self.symbols.get(currency_key, '?')
    
    def get_default_symbol(self) -> str:
        """获取默认货币符号"""
        return self.get_symbol(self.default_currency)
    
    def is_currency_symbol(self, text: str) -> bool:
        """检查文本是否包含货币符号"""
        if not text:
            return False
        return any(symbol.lower() in text.lower() for symbol in self.currency_symbols)
    
    def get_exchange_rate(self, from_currency: str, to_currency: str = 'cny') -> Optional[float]:
        """获取汇率"""
        rate_key = f"{from_currency.lower()}_to_{to_currency.lower()}"
        return self.exchange_rates.get(rate_key)


# 全局货币配置实例
_currency_config: Optional[CurrencyConfig] = None


def get_currency_config() -> CurrencyConfig:
    """获取全局货币配置实例"""
    global _currency_config
    if _currency_config is None:
        _currency_config = CurrencyConfig()
    return _currency_config


def set_currency_config(config: CurrencyConfig):
    """设置全局货币配置实例"""
    global _currency_config
    _currency_config = config
