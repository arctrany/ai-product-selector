"""
网页抓取相关数据模型

定义与网页抓取、数据提取相关的数据结构
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class ScrapingResult:
    """网页抓取结果"""
    success: bool
    data: Dict[str, Any]
    error_message: Optional[str] = None
    execution_time: Optional[float] = None

    def __post_init__(self):
        """数据验证"""
        if self.data is None:
            self.data = {}
