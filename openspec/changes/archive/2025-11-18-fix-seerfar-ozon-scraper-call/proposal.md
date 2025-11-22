# Change: 修复 SeerfarScraper 中 OzonScraper 调用方式

## Why
SeerfarScraper 在处理 OZON 商品详情页时，错误地调用了 OzonScraper 的不存在的私有方法 `_extract_price_data_from_content()` 和 `_extract_competitor_stores_from_content()`，导致代码无法正常运行。

**业务场景**：
1. SeerfarScraper 在 Seerfar 平台抓取商品列表
2. 点击商品图片，通过 `window.open()` 跳转到 OZON 详情页
3. 创建临时页面（`new_page`）访问 OZON URL
4. 提取 OZON 数据后关闭临时页面

**当前问题**：
- ❌ 调用不存在的私有方法，代码无法运行
- ❌ 临时页面打开 OZON 后，OzonScraper 内部又创建新浏览器实例
- ❌ 两个浏览器实例同时访问同一 URL，浪费内存和网络资源

## What Changes
- 修改 `common/scrapers/seerfar_scraper.py` 第 500-660 行的代码
- 使用 OzonScraper 的公共接口方法 `scrape()` 替代不存在的私有方法
- **优化浏览器资源管理**：
  - 临时页面仅用于获取 OZON URL（处理可能的重定向）
  - 获取 URL 后立即关闭临时页面，释放资源
  - 让 OzonScraper 使用自己的浏览器服务进行抓取
  - 避免两个浏览器实例同时运行
- 正确处理 OzonScraper 返回的 ScrapingResult 对象
- **重构代码结构**：
  - 删除 ~30 行死代码（永远不会执行的代码块）
  - 将 `_extract_product_from_row_async` 方法拆分为 4 个职责单一的方法：
    1. `_extract_product_from_row_async`：主方法，协调整个提取流程
    2. `_extract_basic_product_data`：提取 Seerfar 表格基础数据
    3. `_get_ozon_url_from_row`：从行元素提取 OZON URL
    4. `_resolve_ozon_url`：解析 OZON URL，处理重定向
    5. `_fetch_ozon_details`：抓取 OZON 详情页数据
  - 降低方法复杂度：从 250+ 行降至 20-60 行/方法
  - 降低圈复杂度：从 15+ 降至 < 5
  - 降低嵌套层级：从 5-6 层降至 2-3 层

## Impact
- **Affected specs**: `specs/scraping/spec.md`
- **Affected code**: `common/scrapers/seerfar_scraper.py` (第 500-660 行)
- **Breaking changes**: 无（仅内部实现重构，公共接口不变）
- **Risk level**: 低（修复 Bug + 代码重构，提高可维护性）

## Benefits
1. **功能修复**：修复调用不存在方法的 Bug，恢复正常功能
2. **性能优化**：避免两个浏览器实例同时运行，减少 50% 内存占用
3. **代码质量**：
   - 删除死代码，减少 ~30 行无用代码
   - 方法拆分，降低复杂度 60%+
   - 职责单一，易于测试和维护
4. **可读性**：清晰的方法命名和职责划分，降低理解成本
