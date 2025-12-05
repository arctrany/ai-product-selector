# Change: 增加商品输出功能

## Why
当前系统仅支持 `select-shops` 模式（店铺筛选），输出结果为店铺Excel。用户需要 `select-goods` 模式（直接选品），跳过店铺过滤，直接从已知优质店铺中抓取商品，并将符合利润条件的商品输出到独立的商品Excel文件中。

这个功能可以让用户：
- 快速从已知优质店铺中选品，无需重复店铺筛选流程
- 获得标准化的商品清单，便于后续批量上架和管理
- 提高选品效率，减少不必要的数据抓取

## What Changes
- **新增** `ExcelProductWriter` 类，负责将商品数据写入Excel文件
- **修改** `GoodStoreSelector._process_single_store()` 方法，`select-goods` 模式下跳过跟卖信息抓取
- **修改** `GoodStoreSelector._evaluate_products()` 方法，确保商品包含 store_id 信息
- **修改** `GoodStoreSelector._update_excel_results()` 方法，根据 `selection_mode` 选择输出目标（店铺Excel vs 商品Excel）
- **修改** CLI参数验证逻辑，确保 `select-goods` 模式下提供 `item_collect_file` 参数
- **新增** 商品Excel模板格式定义和验证

## Impact
- **影响的规范**: 
  - `cli` - 需要修改用户数据验证逻辑
  - `business-layer` - 需要新增商品输出模块
- **影响的代码**:
  - `common/excel_processor.py` - 新增 `ExcelProductWriter` 类
  - `good_store_selector.py` - 修改 `_process_single_store()`, `_evaluate_products()`, `_update_excel_results()` 方法
  - `cli/main.py` - 修改 `load_user_data()` 和 `handle_start_command()` 验证逻辑
  - `cli/models.py` - 确保 `UIConfig` 包含 `item_collect_file` 字段
  - `common/models/business_models.py` - 确保 `ProductInfo` 包含 `store_id` 字段
- **向后兼容性**: ✅ 完全兼容，不影响现有 `select-shops` 模式
- **性能影响**: 最小化，仅增加商品写入操作，批量写入10条/批
