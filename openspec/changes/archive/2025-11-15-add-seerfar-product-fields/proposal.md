# Change: Add Category, Listing Date, and Sales Volume to Seerfar Product Scraping

## Why
当前 SeerfarScraper 从商品列表表格中提取的数据不完整，缺少类目、上架时间和销量等关键业务字段。这些字段对于商品分析和筛选至关重要：
- **类目**：用于商品分类和市场分析
- **上架时间**：用于评估商品生命周期和新品趋势
- **销量**：用于评估商品热度和市场表现

## What Changes
- 在 `SeerfarScraper._extract_product_from_row_async()` 方法中添加三个新字段的提取逻辑
- 提取类目信息（中文和俄文双语）
- 提取上架时间（日期和天数）
- 提取销量数据
- **新增**：提取商品重量信息（从表格倒数第二列）
- 实现前置过滤机制：在提取基础字段后立即应用 filter_func
- 支持基于类目黑名单、上架时间阈值、销量的组合过滤条件
- **新增**：实现完整的 filter_func，基于用户通过 `--data` 提交的配置进行过滤
- **新增**：修复 `usr_input.json` 字段名拼写错误（item_min_weigt -> item_min_weight）
- **新增**：在 UIConfig 中添加类目黑名单字段支持
- 不符合过滤条件的商品跳过 OZON 详情页处理，提升性能
- 遵循项目编码规范：避免硬编码、返回 `None` 而非默认值、跨平台兼容

## Impact
- 受影响的文件：
  - `common/scrapers/seerfar_scraper.py` - 新增重量提取和完整过滤逻辑
  - `cli/models.py` - UIConfig 新增类目黑名单字段
  - `cli/main.py` - 更新数据加载逻辑以支持新字段
  - `tests/resources/usr_input.json` - 修复字段名拼写错误
- 受影响的功能：Seerfar 商品列表抓取和过滤
- 数据模型变更：商品数据字典新增 4 个字段（类目、上架时间、销量、重量）
- 向后兼容：新增字段为可选，不影响现有功能
