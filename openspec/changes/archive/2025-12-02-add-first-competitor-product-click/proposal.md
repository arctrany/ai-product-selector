# Change: 增加点击first_competitor获取商品ID的功能

## Why
在跟卖店铺抓取流程中，需要获取第一个跟卖店铺的商品ID，以便后续调用OzonScraper抓取该商品的详细信息。当前CompetitorScraper只能获取店铺列表信息，无法获取各店铺销售的具体商品ID。

## What Changes
- **工具类增强** (`common/utils/scraping_utils.py`):
  - 新增`extract_product_id_from_url()`方法，复用现有的URL解析模式，支持从OZON商品URL提取商品ID
- **CompetitorScraper功能扩展** (`common/scrapers/competitor_scraper.py`):
  - 新增`_get_first_competitor_product()`方法，实现点击第一个跟卖店铺并提取商品ID
  - 实现两种提取策略：
    1. DOM提取策略：从页面HTML中直接提取商品链接（快速）
    2. 点击导航策略：点击店铺元素跳转到商品页面提取ID（慢速但可靠）
  - 新增`_extract_product_link_from_element()`方法，支持从DOM中提取商品链接
  - 新增`_click_and_extract_product_id()`方法，支持通过点击跳转提取商品ID
  - **复用工具类**：调用`self.scraping_utils.extract_product_id_from_url()`而不是自己实现
  - 在`scrape()`方法中集成商品ID提取功能，支持通过context参数控制是否提取

## Impact
- 影响的文件: 
  - `common/utils/scraping_utils.py` - 新增商品ID提取工具方法
  - `common/scrapers/competitor_scraper.py` - 核心实现，复用utils工具
  - `common/config/ozon_selectors_config.py` - 可能需要新增选择器配置
  - `tests/integration/test_competitor_scraper_integration.py` - 新增集成测试
  - `tests/unit/test_scraping_utils.py` - 新增工具类单元测试（如文件不存在则创建）
- 影响的模块: 
  - CompetitorScraper数据抓取流程
  - 协调器(Orchestrator)调用流程 - 需要使用返回的商品ID
- 向后兼容: ✅ 完全向后兼容，新功能通过可选参数控制
- 性能影响: 
  - DOM提取策略：几乎无性能影响（<1秒）
  - 点击导航策略：增加3-5秒页面跳转和加载时间
