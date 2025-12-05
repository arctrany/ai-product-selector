# 集成1688图搜API实现货源匹配

## Why

当前系统仅支持OZON平台商品抓取和分析，缺乏货源匹配功能。用户需要手动寻找1688平台的相似商品来确定采购价格，效率低下且容易出错。

通过集成1688图搜代理服务，系统可以：
- 自动根据OZON商品图片搜索1688平台相似商品
- 使用现有图像相似度算法精确匹配最佳货源
- 获取准确的采购价格，提高利润计算准确性
- 实现完整的跨境电商选品闭环

## What Changes

### 核心功能
- **新增** `ImageSearchScraper` 类，通过代理服务器调用1688图搜API
- **新增** `SourceMatcher` 业务逻辑类，实现货源匹配算法
- **扩展** 现有图像相似度工具 `ProductImageSimilarity`，支持批量商品匹配
- **修改** `ScrapingOrchestrator` 支持图搜数据源（可选功能）
- **新增** `ImageSearchProxyConfig` 配置管理

### 数据流程
1. 从OZON商品获取图片URL
2. 通过代理服务器调用1688图搜API获取候选商品列表
3. 使用图像相似度算法匹配最佳货源
4. 返回匹配结果和采购价格信息
5. 集成到现有利润计算流程

### 架构说明
- **同步设计**：所有业务层方法保持同步，符合项目约定（`project.md` 第30行）
- **代理架构**：客户端不直接调用1688 API，通过代理服务器中转，保护敏感凭证
- **可选集成**：图搜功能默认禁用，通过配置启用，不影响现有流程

## Impact

- **影响的规范**:
  - `api-scraper` - 新增图搜抓取器规范
  - `source-matching` - 新增货源匹配规范

- **影响的代码**:
  - `common/scrapers/image_search_scraper.py` - 新增图搜抓取器
  - `common/business/source_matcher.py` - 新增货源匹配业务逻辑
  - `common/services/scraping_orchestrator.py` - 扩展支持图搜功能
  - `common/config/image_search_config.py` - 新增图搜配置管理
  - `common/models/image_search_models.py` - 新增图搜数据模型
  - `utils/image_similarity.py` - 扩展批量匹配功能

- **向后兼容性**: ✅ 完全兼容，作为可选功能集成
- **性能影响**: 最小化，同步API调用，图像匹配可选启用
- **外部依赖**: 需要部署图搜代理服务器（含1688开放平台凭证）

## Technical Notes

- 通过代理服务器调用1688图搜API，客户端仅存储代理地址和客户端API Key
- 复用现有 `utils/image_similarity.py` 图像相似度功能
- 遵循项目架构模式：CLI → Common → 代理服务
- 所有业务层方法保持同步，使用 `requests` 库进行HTTP调用
- 支持本地图像相似度计算，无需外部AI服务依赖