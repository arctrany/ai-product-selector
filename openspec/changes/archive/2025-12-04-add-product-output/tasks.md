# 实施任务清单

## 1. 数据模型和配置 (30分钟)
- [ ] 1.1 确认 `cli/models.py` 的 `UIConfig` 已包含 `item_collect_file` 字段
- [ ] 1.2 确认 `common/models/business_models.py` 的 `ProductInfo` 包含 `store_id` 字段
- [ ] 1.3 修改 `common/config/business_config.py` 的 `ExcelConfig`，添加商品Excel列配置
- [ ] 1.4 在 `common/models/excel_models.py` 添加 `ExcelProductData` 数据类

## 2. 商品Excel写入器实现 (2-3小时)
- [ ] 2.1 在 `common/excel_processor.py` 创建 `ExcelProductWriter` 类
- [ ] 2.2 实现 `__init__()` 方法，初始化商品Excel文件
- [ ] 2.3 实现 `write_product()` 方法（单个商品写入）
- [ ] 2.4 实现 `batch_write_products()` 方法（每10条写入一次）
- [ ] 2.5 实现商品数据格式转换逻辑（`ProductInfo` + 利润数据 → Excel行）
- [ ] 2.6 实现Excel文件初始化和表头写入
- [ ] 2.7 添加单个商品写入失败的错误日志记录

## 3. 主流程修改 (1小时)
- [ ] 3.1 修改 `good_store_selector.py` 的 `_process_single_store()`，select-goods 模式跳过跟卖逻辑
- [ ] 3.2 修改 `_evaluate_products()` 或在输出时为每个商品添加 `store_id`
- [ ] 3.3 修改 `__init__()` 初始化 `ExcelProductWriter`（select-goods 模式）
- [ ] 3.4 修改 `_update_excel_results()` 添加模式判断分支
- [ ] 3.5 实现商品数据收集逻辑（从 `store_results` 提取已筛选商品）
- [ ] 3.6 调用 `ExcelProductWriter.batch_write_products()` 写入商品

## 4. CLI参数验证 (20分钟)
- [ ] 4.1 修改 `cli/main.py` 的 `load_user_data()` 添加 `item_collect_file` 加载
- [ ] 4.2 修改 `handle_start_command()` 添加 select-goods 模式验证
- [ ] 4.3 验证 `item_collect_file` 路径存在性（select-goods 模式必需）
- [ ] 4.4 更新帮助文档和错误提示信息

## 5. 测试和验证 (1-2小时)
- [ ] 5.1 创建单元测试 `tests/unit/test_excel_product_writer.py`
- [ ] 5.2 测试单个商品写入功能
- [ ] 5.3 测试批量商品写入功能（每10条一批）
- [ ] 5.4 测试错误处理（单个商品失败不影响整批）
- [ ] 5.5 测试Excel格式正确性（列对齐、数据类型）
- [ ] 5.6 创建集成测试 `tests/integration/test_select_goods_mode.py`
- [ ] 5.7 端到端测试 select-goods 模式完整流程
- [ ] 5.8 验证跟卖逻辑被正确跳过
- [ ] 5.9 验证 dryrun 模式下的行为正确性

## 6. 文档更新 (30分钟)
- [ ] 6.1 更新 `README.md` 添加 select-goods 模式说明
- [ ] 6.2 创建商品Excel模板示例文件
- [ ] 6.3 更新用户配置模板 `user_data_template_select_goods.json`
- [ ] 6.4 添加商品输出字段说明文档

## 依赖关系
- 任务 2 依赖任务 1（数据模型定义）
- 任务 3 依赖任务 2（写入器实现）
- 任务 4 可与任务 2、3 并行
- 任务 5 依赖任务 1-4 完成
- 任务 6 可在任务 5 完成后进行

## 预计总工作量
**5-7小时**（核心实现 + 测试 + 文档）

## 注意事项
- 利润筛选已在 `_evaluate_products()` 中完成，不需重复筛选
- 单个商品写入失败记录到error日志，不影响整批
- 两种模式都需要更新店铺Excel状态
