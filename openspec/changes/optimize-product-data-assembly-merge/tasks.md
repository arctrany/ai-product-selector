## 1. ScrapingOrchestrator重构 (3天)
- [x] 1.1 简化_orchestrate_product_full_analysis方法
- [x] 1.2 实现_convert_to_product_info数据转换
- [x] 1.3 移除_merge_and_select_best_product方法
- [x] 1.4 移除_evaluate_data_completeness方法
- [x] 1.5 更新相关单元测试

## 2. GoodStoreSelector合并逻辑实现 (4天)
- [x] 2.1 实现merge_and_compute核心方法
- [x] 2.2 实现_evaluate_profit_calculation_completeness评估
- [x] 2.3 实现_prepare_for_profit_calculation数据准备
- [x] 2.4 集成新的数据流到_process_products方法
- [x] 2.5 更新相关业务逻辑测试

## 3. ProductInfo模型增强 (1天)
- [x] 3.1 添加缺失的ERP字段到ProductInfo
- [x] 3.2 添加list_price等衍生字段
- [x] 3.3 更新数据验证逻辑
- [x] 3.4 更新模型相关测试

## 4. 数据结构标准化 (2天)
- [x] 4.1 统一ScrapingResult输出格式
- [x] 4.2 移除冗余字段和调试信息
- [x] 4.3 优化数据传输效率
- [x] 4.4 更新数据序列化逻辑

## 5. 集成测试更新 (2天)
- [x] 5.1 更新产品选择协调集成测试
- [x] 5.2 更新GoodStoreSelector集成测试
- [x] 5.3 创建端到端数据流验证测试
- [x] 5.4 性能基准测试

## 6. 工具函数模块整合 (2天)
- [x] 6.1 增强common/utils/scraping_utils.py工具函数
- [x] 6.2 更新common/models/__init__.py导入路径
- [x] 6.3 删除冗余文件common/models/utils.py和common/utils/model_utils.py
- [x] 6.4 更新所有相关导入语句
- [x] 6.5 验证向后兼容性和功能完整性

## 7. 文档和清理 (1天)
- [x] 7.1 清理废弃代码和注释
- [x] 7.2 更新架构文档
- [x] 7.3 代码审查和最终验证