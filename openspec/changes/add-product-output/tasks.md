# 实施任务清单

## 1. 数据模型和配置 (30分钟)
- [ ] 1.1 修改 `cli/models.py` 的 `UIConfig`，添加 `item_collect_file` 字段
- [ ] 1.2 修改 `common/config/business_config.py` 的 `ExcelConfig`，添加商品Excel列配置
- [ ] 1.3 在 `common/models/excel_models.py` 添加 `ExcelProductData` 数据类

## 2. 商品Excel写入器实现 (2-3小时)
- [ ] 2.1 在 `common/excel_processor.py` 创建 `ExcelProductWriter` 类
- [ ] 2.2 实现 `write_product()` 方法（单个商品写入）
- [ ] 2.3 实现 `batch_write_products()` 方法（批量商品写入）
- [ ] 2.4 实现商品数据格式转换逻辑（`ProductAnalysisResult` → Excel行）
- [ ] 2.5 实现Excel文件初始化和表头写入
- [ ] 2.6 添加数据验证和错误处理

## 3. 主流程修改 (30分钟)
- [ ] 3.1 修改 `good_store_selector.py` 的 `__init__()` 初始化 `ExcelProductWriter`
- [ ] 3.2 修改 `_update_excel_results()` 添加模式判断分支
- [ ] 3.3 实现商品数据收集逻辑（从 `store_results` 提取所有商品）
- [ ] 3.4 调用 `ExcelProductWriter.batch_write_products()` 写入商品

## 4. CLI参数验证 (20分钟)
- [ ] 4.1 修改 `cli/main.py` 的 `load_user_data()` 添加 `item_collect_file` 加载
- [ ] 4.2 修改 `handle_start_command()` 添加 select-goods 模式验证
- [ ] 4.3 验证 `item_collect_file` 路径存在性（select-goods 模式必需）
- [ ] 4.4 更新帮助文档和错误提示信息

## 5. 测试和验证 (1-2小时)
- [ ] 5.1 创建单元测试 `tests/common/test_excel_product_writer.py`
- [ ] 5.2 测试单个商品写入功能
- [ ] 5.3 测试批量商品写入功能
- [ ] 5.4 测试Excel格式正确性（列对齐、数据类型）
- [ ] 5.5 创建集成测试 `tests/integration/test_select_goods_mode.py`
- [ ] 5.6 端到端测试 select-goods 模式完整流程
- [ ] 5.7 验证 dryrun 模式下的行为正确性

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
**4-6小时**（核心实现 + 测试 + 文档）
