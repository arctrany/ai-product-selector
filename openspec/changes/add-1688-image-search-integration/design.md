# 1688图搜API集成设计文档

## 系统架构

### 整体架构图
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   OZON商品      │    │  ScrapingOrches  │    │  1688图搜代理   │
│   (图片URL)     │───▶│  trator          │───▶│   服务器        │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                         │
                              ▼                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  图像相似度     │    │  SourceMatcher   │    │  候选商品列表   │
│  计算引擎       │◀───│  货源匹配器      │◀───│  (1688商品)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌──────────────────┐
                       │   最佳匹配结果   │
                       │  (价格+商品信息) │
                       └──────────────────┘
```

### 安全架构设计
```
客户端(ai-product-selector)        代理服务器(云服务器)        1688开放平台
┌─────────────────────┐           ┌─────────────────────┐    ┌─────────────────┐
│ ImageSearchScraper  │  HTTPS    │ 图搜代理服务         │    │ 1688 API        │
│ - 客户端API Key     │◀─────────▶│ - App Key/Secret    │───▶│ - 商品搜索      │
│ - 图片URL/数据      │           │ - Token管理         │    │ - 图片上传      │
│ - 匹配请求          │           │ - OSS集成           │    └─────────────────┘
└─────────────────────┘           │ - Redis缓存         │
                                  └─────────────────────┘
                                           │
                                           ▼
                                  ┌─────────────────────┐
                                  │ 阿里云OSS存储        │
                                  │ - 图片上传          │
                                  │ - 临时存储          │
                                  └─────────────────────┘
```

### 抓取器层 (`common/scrapers/`)
```python
# common/scrapers/image_search_scraper.py
class ImageSearchScraper:
    """1688图搜代理服务抓取器

    注意：此类不继承 BaseScraper，因为它是纯 API 调用，不涉及浏览器操作。
    遵循项目约定：业务层必须同步，使用 requests 库进行 HTTP 请求。
    """

    def __init__(self, config: ImageSearchProxyConfig):
        self.config = config
        self.session = requests.Session()
        self.logger = logging.getLogger(__name__)

    def search_by_image_url(self, request: ImageSearchRequest) -> ScrapingResult:
        """根据图片URL搜索相似商品（同步方法）"""

    def search_by_image_upload(self, image_data: bytes, params: dict) -> ScrapingResult:
        """上传图片并搜索相似商品（同步方法）"""

    def _call_proxy_api(self, endpoint: str, data: dict) -> dict:
        """调用代理服务器API的通用方法（同步）"""

    def _handle_retry(self, func: Callable, max_retries: int = 3) -> Any:
        """带指数退避的重试机制"""
```

### 业务逻辑层 (`common/business/`)
```python
# common/business/source_matcher.py
class SourceMatcher:
    """货源匹配业务逻辑"""
    
    def __init__(self, similarity_tool: ProductImageSimilarity, config: SourceMatchConfig):
        self.similarity_tool = similarity_tool
        self.config = config
    
    def find_best_match(self, 
                       target_image: str,
                       candidates: List[Api1688Product],
                       similarity_threshold: float = 0.7) -> SourceMatchResult:
        """找到最佳匹配的货源商品"""
        
    def calculate_match_score(self, 
                            target_image: str,
                            candidate: Api1688Product) -> float:
        """计算综合匹配分数"""
        
    def _calculate_price_advantage(self, 
                                  ozon_price: float, 
                                  source_price: float) -> float:
        """计算价格优势"""
```

### 服务编排层 (`common/services/`)
```python
# common/services/scraping_orchestrator.py (扩展现有类)
class ScrapingOrchestrator:
    """扩展编排器支持API数据源

    注意：图搜功能作为可选模块集成，不影响现有浏览器抓取流程。
    所有方法保持同步，符合项目架构约定。
    """

    def __init__(self, ...):
        # 现有初始化代码
        self.image_search_scraper = None  # 延迟初始化
        self.source_matcher = None

    def _init_image_search(self, config: ImageSearchProxyConfig) -> None:
        """按需初始化图搜组件（同步）"""
        if config and config.enabled:
            self.image_search_scraper = ImageSearchScraper(config)
            self.source_matcher = SourceMatcher(
                similarity_tool=ProductImageSimilarity(),
                config=SourceMatchConfig()
            )

    def find_source_match(self, product_info: ProductInfo) -> SourceMatchResult:
        """为商品寻找货源匹配（同步方法）"""

    def _get_1688_candidates(self, image_url: str) -> List[ImageSearchProduct]:
        """获取1688候选商品（同步方法）"""
```

## 模块包结构设计

### 数据模型层 (`common/models/`)
```python
# common/models/api_models.py
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from decimal import Decimal

@dataclass
class ImageSearchProduct:
    """图搜商品信息标准模型"""
    # 基础信息
    product_id: str                    # 商品唯一标识
    title: str                        # 商品标题
    description: Optional[str] = None  # 商品描述
    
    # 价格信息
    price: Decimal                    # 当前价格
    original_price: Optional[Decimal] = None  # 原价
    currency: str = "CNY"             # 货币单位
    
    # 规格信息
    min_order_quantity: int = 1       # 最小起订量
    unit: str = "件"                  # 计量单位
    available_quantity: Optional[int] = None  # 可供数量
    
    # 媒体信息
    main_image_url: str               # 主图URL
    image_urls: List[str]             # 所有图片URLs
    
    # 供应商信息
    supplier_id: str                  # 供应商ID
    supplier_name: str                # 供应商名称
    supplier_location: Optional[str] = None  # 供应商位置
    
    # 分类信息
    category_id: Optional[str] = None # 分类ID
    category_name: Optional[str] = None # 分类名称
    
    # 链接信息
    detail_url: str                   # 商品详情页URL
    
    # 质量评估
    similarity_score: Optional[float] = None  # 相似度分数
    quality_score: Optional[float] = None     # 质量评分

    # 扩展信息（使用 field(default_factory=dict) 避免可变默认值问题）
    attributes: Dict[str, Any] = field(default_factory=dict)
    
@dataclass
class ImageSearchRequest:
    """图搜请求模型"""
    image_url: Optional[str] = None   # 图片URL
    image_data: Optional[bytes] = None # 图片二进制数据
    max_results: int = 20             # 最大结果数
    min_similarity: float = 0.5       # 最小相似度阈值
    price_range: Optional[Dict[str, float]] = None  # 价格范围
    category_filter: Optional[List[str]] = None     # 分类过滤
    supplier_filter: Optional[List[str]] = None    # 供应商过滤

@dataclass
class ImageSearchResponse:
    """图搜响应模型"""
    success: bool                     # 是否成功
    code: int                        # 响应码
    message: str                     # 响应消息
    total: int                       # 总结果数
    products: List[ImageSearchProduct] # 商品列表
    search_id: str                   # 搜索ID
    processing_time: float           # 处理时间(秒)
    error_details: Optional[Dict] = None # 错误详情

@dataclass
class SourceMatchResult:
    """货源匹配结果模型"""
    # 匹配状态
    matched: bool                    # 是否找到匹配
    match_confidence: str            # 匹配置信度: HIGH/MEDIUM/LOW

    # 最佳匹配
    best_match: Optional[ImageSearchProduct] = None
    similarity_score: float = 0.0    # 最高相似度分数

    # 价格分析
    price_advantage: Optional[float] = None  # 价格优势百分比
    estimated_profit_margin: Optional[float] = None  # 预估利润率

    # 所有候选（使用 field(default_factory=list) 避免可变默认值问题）
    all_candidates: List[ImageSearchProduct] = field(default_factory=list)
    candidate_scores: List[float] = field(default_factory=list)

    # 匹配元数据
    search_id: str = ""              # 搜索ID
    match_timestamp: str = ""        # 匹配时间戳
    processing_time: float = 0.0     # 处理耗时
```

### 配置管理层 (`common/config/`)
```python
# common/config/api_config.py
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from .base_config import BaseConfig

@dataclass
class ImageSearchProxyConfig(BaseConfig):
    """图搜代理服务配置"""
    # 代理服务器连接配置
    proxy_host: str                    # 代理服务器主机地址
    proxy_port: int = 8080            # 代理服务器端口
    api_key: str                      # 客户端认证密钥
    use_https: bool = True            # 是否使用HTTPS
    enabled: bool = False             # 是否启用图搜功能
    
    # 网络配置
    connect_timeout: int = 10         # 连接超时(秒)
    read_timeout: int = 30            # 读取超时(秒)
    max_retries: int = 3              # 最大重试次数
    retry_backoff_factor: float = 2.0 # 重试退避因子
    
    # 图片处理配置
    max_image_size_mb: int = 8        # 最大图片大小(MB)
    max_image_dimension: int = 2048   # 最大图片尺寸
    supported_formats: List[str] = field(
        default_factory=lambda: ['jpg', 'jpeg', 'png', 'webp', 'gif']
    )
    auto_resize: bool = True          # 自动调整图片尺寸
    
    # 搜索默认配置
    default_max_results: int = 20     # 默认最大结果数
    default_min_similarity: float = 0.5  # 默认最小相似度
    
    # API端点配置
    endpoints: Dict[str, str] = field(default_factory=lambda: {
        'image_search': '/api/v1/image-search',
        'image_upload': '/api/v1/image-upload',
        'health': '/api/v1/health',
        'auth': '/api/v1/auth/token'
    })
    
    @property
    def base_url(self) -> str:
        """构建代理服务器基础URL"""
        protocol = "https" if self.use_https else "http"
        return f"{protocol}://{self.proxy_host}:{self.proxy_port}"
    
    def get_endpoint_url(self, endpoint_name: str) -> str:
        """获取完整的端点URL"""
        endpoint = self.endpoints.get(endpoint_name, '')
        return f"{self.base_url}{endpoint}"

# common/config/business_config.py (扩展现有文件)
@dataclass
class SourceMatchConfig:
    """货源匹配配置

    注意：相似度计算复用现有 ProductImageSimilarity 类的权重配置，
    此处仅配置货源匹配的业务参数。
    """
    # 匹配置信度阈值
    confidence_thresholds: Dict[str, float] = field(default_factory=lambda: {
        'high': 0.85,      # 高置信度阈值
        'medium': 0.70,    # 中等置信度阈值
        'low': 0.50,       # 低置信度阈值（最低可接受）
    })

    # 快速筛选阈值（用于哈希预筛选，低于此值直接跳过精确计算）
    fast_filter_threshold: float = 0.3

    # 综合评分权重配置
    score_weights: Dict[str, float] = field(default_factory=lambda: {
        'image_similarity': 0.8,  # 图像相似度权重
        'price_advantage': 0.2,   # 价格优势权重
    })

    # 价格因素配置
    price_analysis: Dict[str, Any] = field(default_factory=lambda: {
        'enabled': True,           # 是否考虑价格因素
        'max_price_ratio': 10.0,   # 最大价格比率（1688价格/OZON价格）
        'min_profit_margin': 0.1   # 最小利润率要求
    })

    # 性能配置（同步处理，无并发）
    performance: Dict[str, Any] = field(default_factory=lambda: {
        'max_candidates': 50,          # 最大候选商品数
        'single_match_timeout': 10,    # 单个匹配超时（秒）
        'enable_feature_cache': True,  # 启用特征缓存
        'cache_max_size': 100          # 缓存最大条目数（LRU）
    })

    # 质量过滤配置
    quality_filters: Dict[str, Any] = field(default_factory=lambda: {
        'min_image_size': 200,         # 最小图片尺寸（像素）
        'require_price': True,         # 必须有价格信息
        'require_supplier': True,      # 必须有供应商信息
        'filter_duplicates': True      # 过滤重复商品
    })

@dataclass
class ImageCacheConfig:
    """图片本地缓存配置

    支持多次选品任务复用缓存，减少重复下载。

    工作目录结构（跨平台统一使用 ~/.xp/）：
    ~/.xp/
    ├── configs/        # 配置目录（现有，xp_cli.py使用）
    ├── presets/        # 预设目录（需迁移，原 ~/.xuanping/presets/）
    ├── data/           # 数据目录（需迁移，原 ~/.xuanping/data/）
    ├── logs/           # 日志目录（需迁移，原 ~/.xuanping/data/logs/）
    └── cache/          # 缓存目录（新增）
        └── images/     # 图片缓存
            ├── ozon/
            ├── 1688/
            └── features/

    注意：现有代码中 .xuanping 和 .xp 混用，此设计统一使用 .xp。
    实现时需同步更新 common/logging_config.py 和 cli/preset_manager.py。
    """
    # 缓存目录配置（跨平台统一使用 .xp 工作目录）
    cache_base_dir: str = field(default_factory=lambda: os.path.join(
        os.path.expanduser('~'), '.xp', 'cache', 'images'
    ))

    # 缓存子目录结构
    # {cache_base_dir}/
    #   ├── ozon/           # OZON商品图片
    #   │   └── {hash}.jpg
    #   ├── 1688/           # 1688候选商品图片
    #   │   └── {hash}.jpg
    #   └── features/       # CLIP特征向量缓存（pickle格式）
    #       └── {hash}.pkl

    # 缓存策略
    enabled: bool = True                    # 是否启用图片缓存
    max_cache_size_gb: float = 5.0          # 最大缓存大小（GB）
    cache_ttl_days: int = 7                 # 缓存有效期（天）
    cleanup_on_startup: bool = True         # 启动时清理过期缓存

    # 下载配置
    download_timeout: int = 30              # 单张图片下载超时（秒）
    download_retries: int = 3               # 下载重试次数
    download_retry_delay: float = 1.0       # 重试间隔（秒）

    # 图片处理
    resize_for_cache: bool = True           # 缓存前压缩图片
    cache_image_max_size: int = 800         # 缓存图片最大尺寸（像素）
    cache_image_quality: int = 85           # JPEG压缩质量

    # 请求头配置（处理防盗链）
    default_headers: Dict[str, str] = field(default_factory=lambda: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
    })
    # 1688图片可能需要特定Referer
    platform_headers: Dict[str, Dict[str, str]] = field(default_factory=lambda: {
        '1688': {'Referer': 'https://www.1688.com/'},
        'ozon': {'Referer': 'https://www.ozon.ru/'},
    })

    def get_cache_dir(self, platform: str) -> Path:
        """获取指定平台的缓存目录"""
        cache_dir = Path(self.cache_base_dir) / platform
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir

    def get_cache_path(self, image_url: str, platform: str) -> Path:
        """根据图片URL生成缓存文件路径"""
        import hashlib
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        return self.get_cache_dir(platform) / f"{url_hash}.jpg"

    def get_feature_cache_path(self, image_url: str) -> Path:
        """获取CLIP特征缓存路径"""
        import hashlib
        url_hash = hashlib.md5(image_url.encode()).hexdigest()
        feature_dir = Path(self.cache_base_dir) / 'features'
        feature_dir.mkdir(parents=True, exist_ok=True)
        return feature_dir / f"{url_hash}.pkl"
```

## 图片缓存管理器设计

```python
# common/services/image_cache_manager.py
import os
import time
import pickle
import hashlib
import logging
from pathlib import Path
from typing import Optional, Tuple
from PIL import Image
import requests

class ImageCacheManager:
    """图片缓存管理器

    功能：
    1. 下载图片并缓存到本地磁盘
    2. 支持多次选品任务复用缓存
    3. 自动清理过期缓存
    4. 处理防盗链问题
    """

    def __init__(self, config: ImageCacheConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._init_cache_dirs()
        if config.cleanup_on_startup:
            self._cleanup_expired_cache()

    def _init_cache_dirs(self):
        """初始化缓存目录"""
        Path(self.config.cache_base_dir).mkdir(parents=True, exist_ok=True)

    def get_image(self, image_url: str, platform: str = 'unknown') -> Optional[Image.Image]:
        """获取图片（优先从缓存读取，缓存未命中则下载）

        Args:
            image_url: 图片URL
            platform: 平台标识（'ozon', '1688'等）

        Returns:
            PIL Image对象，失败返回None
        """
        cache_path = self.config.get_cache_path(image_url, platform)

        # 检查缓存
        if self._is_cache_valid(cache_path):
            self.logger.debug(f"缓存命中: {cache_path}")
            return self._load_from_cache(cache_path)

        # 下载图片
        image = self._download_image(image_url, platform)
        if image:
            self._save_to_cache(image, cache_path)

        return image

    def _is_cache_valid(self, cache_path: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_path.exists():
            return False
        # 检查TTL
        file_age_days = (time.time() - cache_path.stat().st_mtime) / 86400
        return file_age_days < self.config.cache_ttl_days

    def _download_image(self, url: str, platform: str) -> Optional[Image.Image]:
        """下载图片（带重试和防盗链处理）"""
        headers = self.config.default_headers.copy()
        if platform in self.config.platform_headers:
            headers.update(self.config.platform_headers[platform])

        for attempt in range(self.config.download_retries):
            try:
                response = requests.get(
                    url,
                    headers=headers,
                    timeout=self.config.download_timeout
                )
                response.raise_for_status()
                image = Image.open(BytesIO(response.content)).convert('RGB')

                # 压缩图片以节省磁盘空间
                if self.config.resize_for_cache:
                    image = self._resize_image(image)

                return image
            except Exception as e:
                self.logger.warning(f"下载图片失败 (尝试 {attempt+1}/{self.config.download_retries}): {e}")
                if attempt < self.config.download_retries - 1:
                    time.sleep(self.config.download_retry_delay * (attempt + 1))

        return None

    def _cleanup_expired_cache(self):
        """清理过期缓存"""
        # 实现略：遍历缓存目录，删除超过TTL的文件
        pass

    def get_cache_stats(self) -> dict:
        """获取缓存统计信息"""
        # 返回缓存大小、文件数、命中率等
        pass

    def clear_cache(self, platform: Optional[str] = None):
        """清空缓存"""
        pass
```

## 技术实现细节

### 1. 代理服务器通信
- 使用HTTPS协议确保传输安全
- 客户端API Key认证，避免直接暴露1688凭证
- 请求签名验证防止篡改
- 支持多环境配置（开发/生产代理服务器）

### 2. 安全的图像处理流程
```python
# 客户端处理流程
1. 图片预处理：压缩、格式验证
2. 通过代理服务器上传到OSS（如需要）
3. 发送搜索请求到代理服务器
4. 代理服务器处理1688 API调用
5. 返回标准化商品数据
```

### 3. 代理服务器API接口设计
```python
# 代理服务器标准RESTful API
POST /api/v1/image-search
Headers: 
  - Authorization: Bearer {client_api_key}
  - Content-Type: application/json
Body: {
  "imageUrl": "https://example.com/image.jpg",
  "searchParams": {
    "maxResults": 20,
    "minSimilarity": 0.7,
    "priceRange": {"min": 0, "max": 10000}
  }
}
Response: {
  "code": 200,
  "message": "success",
  "data": {
    "total": 15,
    "products": [...],
    "searchId": "uuid-search-id",
    "processingTime": 2.5
  }
}

POST /api/v1/image-upload
Headers: 
  - Authorization: Bearer {client_api_key}
  - Content-Type: multipart/form-data
Body: FormData {
  "image": File,
  "searchParams": JSON
}
Response: {
  "code": 200,
  "data": {
    "imageUrl": "https://oss.example.com/temp/image.jpg",
    "searchResults": {...}
  }
}

GET /api/v1/health
Response: {
  "code": 200,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-12-04T10:30:00Z",
    "dependencies": {
      "1688_api": "connected",
      "oss": "connected",
      "redis": "connected"
    }
  }
}

POST /api/v1/auth/token
Headers: X-API-Key: {client_api_key}
Response: {
  "code": 200,
  "data": {
    "accessToken": "jwt_token",
    "expiresIn": 3600,
    "tokenType": "Bearer"
  }
}
```

### 4. 客户端安全设计
- 仅存储代理服务器地址和客户端API Key
- 敏感的1688凭证完全在代理服务器管理
- OSS临时凭证通过代理服务器安全获取
- 本地不缓存敏感信息

### 5. 错误处理和重试
- 网络超时重试（指数退避）
- 代理服务器错误处理
- 图片处理错误降级
- 详细错误日志记录

### 6. 性能优化
- 并发图像相似度计算
- 客户端结果缓存（非敏感数据）
- 批量处理支持
- 内存使用优化

### 工具扩展层 (`utils/`)
```python
# utils/image_similarity.py (扩展现有文件)
class ProductImageSimilarity:
    """扩展现有图像相似度工具，支持商品匹配场景"""
    
    def batch_calculate_similarity(self, 
                                 target_image: str,
                                 candidate_images: List[str],
                                 max_concurrent: int = 5) -> List[float]:
        """批量并发计算图像相似度"""
        
    def calculate_product_match_score(self, 
                                    target_image: str,
                                    candidate_image: str,
                                    use_enhanced_algorithm: bool = True) -> float:
        """专门用于商品匹配的相似度计算"""
```

### CLI集成层 (`cli/`)
```python
# cli/models.py (扩展现有UIConfig)
@dataclass
class UIConfig:
    # 现有字段...
    
    # 1688匹配配置
    enable_1688_matching: bool = False
    api_1688_similarity_threshold: float = 0.7
    api_1688_max_results: int = 10

# cli/main.py (扩展现有功能)
def load_user_data(config_path: str) -> UIConfig:
    """加载用户配置，包括1688匹配设置"""
    # 现有逻辑...
    # 添加1688配置验证
```

### 测试层 (`tests/`)
```python
# tests/unit/test_api_1688_scraper.py
# tests/unit/test_source_matcher.py
# tests/integration/test_1688_integration.py
# tests/performance/test_image_matching_performance.py
```

## 完整包结构总览

```
ai-product-selector3/
├── common/
│   ├── models/
│   │   ├── image_search_models.py  # 🆕 图搜数据模型
│   │   └── __init__.py             # 导出新模型
│   ├── config/
│   │   ├── image_search_config.py  # 🆕 图搜代理服务配置
│   │   └── business_config.py      # 📝 扩展货源匹配配置
│   ├── scrapers/
│   │   └── image_search_scraper.py # 🆕 图搜抓取器
│   ├── business/
│   │   └── source_matcher.py       # 🆕 货源匹配业务逻辑
│   └── services/
│       └── scraping_orchestrator.py # 📝 扩展支持图搜功能
├── utils/
│   └── image_similarity.py         # 📝 扩展商品匹配功能
├── cli/
│   ├── models.py                   # 📝 扩展UI配置
│   └── main.py                     # 📝 集成图搜匹配功能
└── tests/
    ├── unit/
    │   ├── test_image_search_scraper.py  # 🆕 图搜抓取器测试
    │   └── test_source_matcher.py        # 🆕 货源匹配测试
    ├── integration/
    │   └── test_image_search_integration.py # 🆕 端到端集成测试
    └── performance/
        └── test_image_matching_performance.py # 🆕 性能测试

图例: 🆕 新增文件 | 📝 扩展现有文件
```

## 集成点设计

### 与现有系统集成
1. **GoodStoreSelector集成**
   - 在商品分析流程中调用货源匹配
   - 将匹配结果用于利润计算
   - 可选启用/禁用货源匹配功能

2. **利润计算集成**
   - 使用匹配到的1688价格作为采购价
   - 更新利润计算逻辑
   - 提供价格对比分析

3. **Excel输出集成**
   - 在商品Excel中添加货源匹配信息
   - 显示匹配相似度和价格优势
   - 提供1688商品链接

## 部署和运维

### 外部依赖
- 1688开放平台账号和API权限
- 阿里云OSS存储（用于图片上传）
- 可选：Redis缓存服务

### 客户端配置要求
```yaml
# 环境变量配置
API_1688_PROXY_HOST: "your-ecs-ip"
API_1688_PROXY_PORT: "8080"
API_1688_USE_HTTPS: "false"  # 内网可用HTTP，公网建议HTTPS
API_1688_API_KEY: "your_client_api_key"
API_1688_ENABLED: "true"
API_1688_TIMEOUT: "30"
API_1688_MAX_RETRIES: "3"
```

### 代理服务器配置要求
```yaml
# 代理服务器环境变量（在ECS上配置）
ALIBABA_1688_APP_KEY: "your_1688_app_key"
ALIBABA_1688_APP_SECRET: "your_1688_app_secret"
OSS_ENDPOINT: "oss-cn-hangzhou.aliyuncs.com"
OSS_ACCESS_KEY_ID: "your_oss_key"
OSS_ACCESS_KEY_SECRET: "your_oss_secret"
OSS_BUCKET_NAME: "your_bucket"
REDIS_HOST: "localhost"
REDIS_PORT: "6379"
CLIENT_API_KEYS: "key1,key2,key3"  # 允许的客户端API Key列表
```

### 监控和日志
- API调用成功率监控
- 图像相似度计算性能监控
- 匹配准确率统计
- 详细的调试日志

## 安全考虑

### 客户端安全
- 仅存储代理服务器地址和客户端API Key
- 使用HTTPS通信（生产环境）
- 请求签名验证防篡改
- 本地不存储敏感的1688凭证

### 代理服务器安全
- 1688 App Key/Secret安全存储在服务器端
- 客户端API Key白名单验证
- 请求频率限制和防刷机制
- OSS临时凭证动态生成

### 数据安全
- 图片URL验证和过滤
- 敏感信息脱敏处理
- 临时图片自动清理
- 用户数据隐私保护

## 测试策略

### 单元测试
- API抓取器功能测试
- 图像相似度算法测试
- 匹配逻辑测试
- 配置管理测试

### 集成测试
- 端到端货源匹配流程测试
- API服务集成测试
- 图像处理集成测试
- 错误场景测试

### 性能测试
- API响应时间测试
- 图像相似度计算性能测试
- 并发处理能力测试
- 内存使用测试