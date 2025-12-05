# 任务清单

## 阶段1: 基础设施 (17个任务)

### 1.1 数据模型和配置
- [ ] 1.1.1 创建 `common/models/image_search_models.py`，定义 `ImageSearchProduct`、`ImageSearchRequest`、`ImageSearchResponse`、`SourceMatchResult` 数据类
- [ ] 1.1.2 创建 `common/config/image_search_config.py`，定义 `ImageSearchProxyConfig` 和 `SourceMatchConfig` 配置类
- [ ] 1.1.3 在 `common/models/__init__.py` 和 `common/config/__init__.py` 中导出新模型
- [ ] 1.1.4 编写数据模型和配置的单元测试

### 1.2 统一工作目录
- [ ] 1.2.1 更新 `common/logging_config.py`，将 `.xuanping` 改为 `.xp`
- [ ] 1.2.2 更新 `cli/preset_manager.py`，将 `.xuanping/presets` 改为 `.xp/presets`
- [ ] 1.2.3 添加向后兼容：首次启动时自动迁移旧目录数据到新目录

### 1.3 图片缓存管理器
- [ ] 1.3.1 在 `common/config/image_search_config.py` 中添加 `ImageCacheConfig` 配置类
- [ ] 1.3.2 创建 `common/services/image_cache_manager.py`，实现 `ImageCacheManager` 类
- [ ] 1.3.3 实现缓存目录结构（~/.xp/cache/images/，按平台分类：ozon/、1688/、features/）
- [ ] 1.3.4 实现防盗链处理（平台特定Referer和User-Agent）
- [ ] 1.3.5 实现缓存TTL检查和过期清理
- [ ] 1.3.6 创建 `tests/unit/test_image_cache_manager.py`，编写缓存管理器单元测试

### 1.4 图搜抓取器实现
- [ ] 1.4.1 创建 `common/scrapers/image_search_scraper.py`，实现 `ImageSearchScraper` 类（同步HTTP调用）
- [ ] 1.4.2 实现代理服务器认证、错误处理和指数退避重试机制
- [ ] 1.4.3 实现响应数据验证和标准化转换
- [ ] 1.4.4 创建 `tests/unit/test_image_search_scraper.py`，编写抓取器单元测试

## 阶段2: 货源匹配算法 (10个任务)

### 2.1 修复现有图像相似度工具问题
- [ ] 2.1.1 修复 `CLIPSimilarityCalculator` 缓存机制：使用图片内容哈希替代对象ID作为缓存键
- [ ] 2.1.2 实现 LRU 缓存策略（`functools.lru_cache` 或自定义），限制最大缓存100个特征
- [ ] 2.1.3 在 `load_image_from_source` 中添加重试机制和更好的错误处理

### 2.2 图像相似度工具扩展
- [ ] 2.2.1 在 `utils/image_similarity.py` 中添加 `batch_calculate_similarity` 批量计算方法（同步顺序处理）
- [ ] 2.2.2 添加 `calculate_fast_hash_only` 用于快速预筛选（仅哈希，不加载CLIP）
- [ ] 2.2.3 编写图像相似度扩展和修复的单元测试

### 2.3 货源匹配器实现
- [ ] 2.3.1 创建 `common/business/source_matcher.py`，实现 `SourceMatcher` 类
- [ ] 2.3.2 集成 `ImageCacheManager`，通过缓存管理器获取图片
- [ ] 2.3.3 实现多层次匹配策略（快速哈希筛选阈值0.3 + 精确CLIP匹配）和置信度评估
- [ ] 2.3.4 创建 `tests/unit/test_source_matcher.py`，编写货源匹配单元测试

## 阶段3: 系统集成 (6个任务)

### 3.1 编排器集成
- [ ] 3.1.1 扩展 `ScrapingOrchestrator`，添加图搜组件延迟初始化和 `find_source_match` 方法
- [ ] 3.1.2 实现匹配失败的降级处理逻辑
- [ ] 3.1.3 编写编排器图搜集成测试

### 3.2 业务流程集成
- [ ] 3.2.1 修改 `ProfitEvaluator`，支持使用1688匹配价格作为采购价
- [ ] 3.2.2 扩展 `ExcelProcessor`，添加货源匹配信息列（相似度、价格优势、1688链接）
- [ ] 3.2.3 在CLI中添加图搜功能开关和进度显示

## 阶段4: 测试和文档 (4个任务)

### 4.1 集成测试
- [ ] 4.1.1 创建 `tests/integration/test_image_search_integration.py`，编写端到端集成测试
- [ ] 4.1.2 创建 `tests/performance/test_image_matching_performance.py`，编写性能基准测试

### 4.2 文档和部署
- [ ] 4.2.1 编写图搜功能使用文档（配置说明、API参考）
- [ ] 4.2.2 更新系统配置文档，添加代理服务器部署指南

## 验收标准

### 功能验收
- ✅ 能够通过OZON商品图片搜索1688相似商品
- ✅ 图像相似度匹配准确率 ≥ 80%（基于测试数据集）
- ✅ API调用成功率 ≥ 95%（正常网络条件下）
- ✅ 匹配结果正确集成到利润计算和Excel输出

### 性能验收
- ✅ 单个商品货源匹配时间 ≤ 10秒（缓存命中时 ≤ 3秒）
- ✅ 批量处理100个商品 ≤ 15分钟（首次），≤ 5分钟（缓存命中）
- ✅ 内存使用增长 ≤ 200MB
- ✅ 图片缓存命中率 ≥ 60%（多次任务场景）

### 质量验收
- ✅ 单元测试覆盖率 ≥ 85%
- ✅ 集成测试覆盖核心业务场景
- ✅ 错误处理和降级机制完善
- ✅ 日志记录详细且结构化
