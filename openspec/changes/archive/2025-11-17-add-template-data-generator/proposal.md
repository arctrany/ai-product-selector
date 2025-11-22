# Change: 添加模板数据生成器

## Why

当前用户需要手动创建 JSON 配置文件，且不清楚不同选择模式（`--select-shops` 和 `--select-goods`）需要哪些配置字段。这导致：
1. 用户体验差，需要查看文档或示例才能知道需要哪些字段
2. 容易遗漏必需字段或包含不必要的字段
3. 不同模式的配置差异不明确

## What Changes

添加 `--create-template-data` 命令行选项，根据选择模式自动生成对应的 JSON 模板文件：

- **select-shops 模式模板**：包含店铺筛选所需的所有字段
  - 必需字段：`good_shop_file`, `margin_calculator`
  - 店铺过滤字段：`min_store_sales_30days`, `min_store_orders_30days`
  - 商品过滤字段：`margin`, `item_shelf_days`, `follow_buy_cnt`, `max_monthly_sold`, `monthly_sold_min`, `item_min_weight`, `item_max_weight`, `g01_item_min_price`, `g01_item_max_price`, `max_products_per_store`
  - 输出设置：`output_format`, `output_path`（如未指定，默认输出到当前目录）

- **select-goods 模式模板**：包含直接选品所需的字段
  - 必需字段：`good_shop_file`, `item_collect_file`, `margin_calculator`
  - 商品过滤字段：同上
  - 输出设置：同上
  - **不包含**：店铺过滤字段（因为此模式跳过店铺筛选）

- 清理冗余字段：
  - 移除 `item_created_days`（未在实际代码中使用，与 `item_shelf_days` 含义重复）
  - 移除 `category_blacklist`（应该在系统配置 `--config` 中而非用户数据 `--data` 中）
  - `remember_settings` 和 `dryrun` 保留在 UIConfig 中，但不应出现在生成的模板文件中（这些是 CLI 运行时参数）

## Impact

- **影响的 specs**：`cli` (命令行界面)
- **影响的代码**：
  - `cli/main.py`：添加模板生成逻辑和新的命令行选项
  - `cli/models.py`：可能需要添加模板生成方法
- **向后兼容性**：完全兼容，仅添加新功能
- **用户体验**：显著改善，用户可以快速生成正确的配置模板
