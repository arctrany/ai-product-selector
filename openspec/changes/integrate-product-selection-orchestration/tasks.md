## 1. OzonScraper增强
- [x] 1.1 添加include_competitor参数支持
- [x] 1.2 集成FilterManager和ProfitEvaluator
- [x] 1.3 实现_should_analyze_competitor方法
- [x] 1.4 实现跟卖商品详情抓取逻辑

## 2. ScrapingOrchestrator职责调整
- [x] 2.1 重构_orchestrate_product_full_analysis方法
- [x] 2.2 实现_merge_and_select_best_product方法
- [x] 2.3 实现_evaluate_data_completeness方法
- [x] 2.4 实现_build_competitor_url方法

## 3. GoodStoreSelector适配
- [x] 3.1 更新商品处理调用参数
- [x] 3.2 适配新的返回数据结构

## 4. 测试和验证
- [x] 4.1 更新OzonScraper单元测试
- [x] 4.2 更新ScrapingOrchestrator单元测试
- [x] 4.3 端到端集成测试
- [x] 4.4 回归测试验证