# Change: 重构 Seerfar Scraper 统一抓取接口

## Why
当前 `good_store_selector.py` 需要分别调用 `seerfar_scraper.scrape_store_sales_data()` 和 `seerfar_scraper.scrape_store_products()` 两个方法来获取店铺的完整信息，导致：

1. **职责混乱**：业务层需要了解 scraper 的内部实现细节
2. **代码重复**：需要手动组合两次调用的结果
3. **过滤逻辑外置**：过滤函数在外部创建并注入，增加了耦合度
4. **维护困难**：修改抓取逻辑需要同时修改多处代码

## What Changes
- **重构 `seerfar_scraper.scrape()` 方法**：增强为统一的抓取接口，支持过滤函数注入，整合销售数据和商品抓取
- **删除冗余方法**：移除 `seerfar_scraper.scrape_store_products()` 和 `good_store_selector._scrape_store_products()` 方法
- **简化 `good_store_selector.py`**：使用单一的 `scrape()` 调用替代多次调用

### 具体变更
1. **重构 `seerfar_scraper.scrape()` 方法**：
   - 添加 `max_products` 参数：控制最大商品数量
   - 添加 `product_filter_func` 参数：支持商品前置过滤
   - 添加 `store_filter_func` 参数：支持店铺过滤（可选）
   - 整合 `scrape_store_sales_data()` 和商品抓取逻辑到一个方法中

2. **删除 `seerfar_scraper.scrape_store_products()` 方法**：
   - **BREAKING CHANGE**: 该方法将被删除，功能已完全整合到 `scrape()` 中
   - 所有调用方需要迁移到使用 `scrape()` 方法

3. **修改 `good_store_selector._process_single_store()` 方法**：
   - 使用 `seerfar_scraper.scrape()` 替代分步调用
   - 通过依赖注入传递过滤函数
   - 简化结果处理逻辑

4. **删除 `good_store_selector._scrape_store_products()` 方法**：
   - 该方法的功能已被 `seerfar_scraper.scrape()` 完全覆盖

## Impact
- **受影响的 specs**: `seerfar-scraper`
- **受影响的代码**: 
  - `common/scrapers/seerfar_scraper.py` (重构 `scrape()` 方法，**删除** `scrape_store_products()` 方法)
  - `good_store_selector.py` (简化 `_process_single_store()` 方法，删除 `_scrape_store_products()` 方法)
- **受影响的测试**: 
  - `tests/test_selection_modes_real.py` (需要更新 mock 调用，移除对 `scrape_store_products()` 的引用)
- **⚠️ BREAKING CHANGE**: 删除 `seerfar_scraper.scrape_store_products()` 方法，所有外部调用需要迁移

## Benefits
1. **职责清晰**：scraper 负责所有抓取逻辑，业务层只负责编排
2. **代码简洁**：一次调用完成所有抓取和过滤
3. **易于维护**：修改抓取逻辑只需修改 scraper
4. **性能优化**：支持店铺级别的提前过滤，避免不必要的商品抓取
5. **更好的测试性**：单一接口更容易 mock 和测试
