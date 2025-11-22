## MODIFIED Requirements

### Requirement: 用户数据加载
系统必须（MUST）从 JSON 文件加载用户配置，并应当（SHALL）忽略未识别的字段以保持向后兼容性。

#### Scenario: 加载包含已废弃字段的配置
- **WHEN** 用户加载包含 `item_created_days` 或 `category_blacklist` 的配置文件
- **THEN** 系统应当成功加载配置
- **AND** 显示警告消息提示这些字段已废弃
- **AND** 忽略 `item_created_days` 和 `category_blacklist` 字段
- **AND** 使用 `item_shelf_days` 字段（如果提供）或默认值
- **AND** 类目黑名单应当从系统配置文件（`--config`）的 `selector_filter.item_category_blacklist` 读取

#### Scenario: 加载不完整的配置
- **WHEN** 用户加载的配置文件缺少某些可选字段
- **THEN** 系统应当使用默认值填充缺失的字段
- **AND** 成功加载配置

#### Scenario: output_path 未指定时使用默认值
- **WHEN** 用户加载的配置文件中 `output_path` 为空字符串或未提供
- **THEN** 系统应当将输出路径设置为当前工作目录
- **AND** 成功执行任务并将结果输出到当前目录

## MODIFIED Requirements

### Requirement: 模板数据生成
系统必须（MUST）提供命令行选项来生成不同选择模式的配置模板文件，帮助用户快速创建正确的配置。

#### Scenario: 生成 select-shops 模式模板
- **WHEN** 用户执行 `python cli/main.py --create-template-data --mode select-shops`
- **THEN** 系统应当在当前目录生成 `template_select_shops.json` 文件
- **AND** 文件应当包含以下字段及其默认值：
  - `good_shop_file`: "/path/to/good_shops.xlsx"
  - `margin_calculator`: "/path/to/margin_calculator.xlsx"
  - `margin`: 0.15
  - `item_shelf_days`: 150
  - `follow_buy_cnt`: 50
  - `max_monthly_sold`: 1000
  - `monthly_sold_min`: 150
  - `item_min_weight`: 0
  - `item_max_weight`: 2000
  - `g01_item_min_price`: 10
  - `g01_item_max_price`: 500
  - `min_store_sales_30days`: 500000.0
  - `min_store_orders_30days`: 250
  - `max_products_per_store`: 50
  - `output_format`: "xlsx"
  - `output_path`: "/path/to/output/"
- **AND** 文件**不应当**包含已废弃的 `category_blacklist` 字段
- **AND** 文件应当包含注释说明每个字段的用途
- **AND** 注释应当说明类目黑名单配置位于系统配置文件中

#### Scenario: 生成 select-goods 模式模板
- **WHEN** 用户执行 `python cli/main.py --create-template-data --mode select-goods`
- **THEN** 系统应当在当前目录生成 `template_select_goods.json` 文件
- **AND** 文件应当包含以下字段及其默认值：
  - `good_shop_file`: "/path/to/good_shops.xlsx"
  - `item_collect_file`: "/path/to/item_collect.xlsx"
  - `margin_calculator`: "/path/to/margin_calculator.xlsx"
  - `margin`: 0.15
  - `item_shelf_days`: 150
  - `follow_buy_cnt`: 50
  - `max_monthly_sold`: 1000
  - `monthly_sold_min`: 150
  - `item_min_weight`: 0
  - `item_max_weight`: 2000
  - `g01_item_min_price`: 10
  - `g01_item_max_price`: 500
  - `max_products_per_store`: 50
  - `output_format`: "xlsx"
  - `output_path`: "/path/to/output/"
- **AND** 文件**不应当**包含店铺过滤字段（`min_store_sales_30days`, `min_store_orders_30days`）
- **AND** 文件**不应当**包含已废弃的 `category_blacklist` 字段
- **AND** 文件应当包含注释说明每个字段的用途
- **AND** 注释应当说明类目黑名单配置位于系统配置文件中

#### Scenario: 指定输出路径
- **WHEN** 用户执行 `python cli/main.py --create-template-data --mode select-shops --output /custom/path/my_template.json`
- **THEN** 系统应当在指定路径生成模板文件
- **AND** 如果目录不存在，应当自动创建

#### Scenario: 模式参数缺失
- **WHEN** 用户执行 `python cli/main.py --create-template-data` 但未指定 `--mode`
- **THEN** 系统应当显示错误消息："错误：--create-template-data 需要指定 --mode 参数（select-shops 或 select-goods）"
- **AND** 退出码应当为 1

#### Scenario: 模式参数无效
- **WHEN** 用户执行 `python cli/main.py --create-template-data --mode invalid-mode`
- **THEN** 系统应当显示错误消息："错误：无效的模式 'invalid-mode'，可用模式：select-shops, select-goods"
- **AND** 退出码应当为 1

#### Scenario: 文件已存在
- **WHEN** 用户执行模板生成命令但目标文件已存在
- **THEN** 系统应当提示用户："文件已存在，是否覆盖？(y/n)"
- **AND** 如果用户输入 'y'，则覆盖文件
- **AND** 如果用户输入 'n'，则取消操作并退出
