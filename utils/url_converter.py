"""
URL 转换工具模块

提供各种 URL 转换功能，避免在业务代码中硬编码
"""

import re
import logging
from typing import Optional


logger = logging.getLogger(__name__)


def convert_image_url_to_product_url(image_url: str) -> Optional[str]:
    """
    从图片URL转换为商品页面URL
    
    Args:
        image_url: 图片URL
        
    Returns:
        Optional[str]: 商品页面URL，如果转换失败返回None
        
    Examples:
        >>> convert_image_url_to_product_url("https://cdn1.ozone.ru/s3/multimedia-x/wc1000/6123456789.jpg")
        'https://www.ozon.ru/product/-123456789/'
    """
    try:
        if not image_url:
            return None
        
        # 从图片URL中提取商品ID
        # 常见的OZON图片URL格式：
        # https://cdn1.ozone.ru/s3/multimedia-x/wc1000/6123456789.jpg
        # 对应的商品页面URL：
        # https://www.ozon.ru/product/product-name-123456789/
        
        # 提取数字ID（通常是文件名中的数字部分）
        match = re.search(r'/(\d+)\.(?:jpg|jpeg|png|webp)', image_url, re.IGNORECASE)
        if not match:
            # 尝试其他模式
            match = re.search(r'(\d{8,})', image_url)
        
        if match:
            product_id = match.group(1)
            # 构建OZON商品页面URL
            product_url = f"https://www.ozon.ru/product/-{product_id}/"
            logger.debug(f"转换图片URL到商品URL: {image_url} -> {product_url}")
            return product_url
        
        # 如果无法提取ID，尝试直接使用图片URL作为商品URL的基础
        # 这是一个备用方案，可能需要根据实际情况调整
        if 'ozon.ru' in image_url or 'ozone.ru' in image_url:
            # 如果是OZON的图片，尝试构建基础URL
            filename = image_url.split('/')[-1].split('.')[0]
            if filename and filename.isdigit():
                return f"https://www.ozon.ru/product/-{filename}/"
        
        logger.warning(f"无法从图片URL提取商品ID: {image_url}")
        return None
        
    except Exception as e:
        logger.error(f"转换图片URL失败: {e}")
        return None
