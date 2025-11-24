## ADDED Requirements

### Requirement: Select-Goods 模式商品文件配置
系统必须（MUST）在 select-goods 模式下接受商品收集文件路径作为必需参数，用于指定商品输出的目标Excel文件。

#### Scenario: 提供商品收集文件路径
- **WHEN** 用户在 select-goods 模式下提供 `item_collect_file` 参数
- **THEN** 系统应当接受该参数并用于商品输出
- **AND** 验证文件路径格式正确（.xlsx 扩展名）
- **AND** 如果文件不存在，自动创建新文件
- **AND** 如果文件已存在，追加写入商品数据

#### Scenario: Select-Goods 模式缺少商品文件参数
- **WHEN** 用户在 select-goods 模式下未提供 `item_collect_file` 参数
- **THEN** 系统应当显示错误消息："错误：select-goods 模式需要提供 item_collect_file 参数"
- **AND** 退出码应当为 1
- **AND** 不执行任何商品抓取操作

#### Scenario: Select-Shops 模式忽略商品文件参数
- **WHEN** 用户在 select-shops 模式下提供 `item_collect_file` 参数
- **THEN** 系统应当忽略该参数
- **AND** 显示信息消息："注意：select-shops 模式不使用 item_collect_file 参数"
- **AND** 正常执行店铺筛选流程

#### Scenario: 商品文件路径无效
- **WHEN** 用户提供的 `item_collect_file` 路径包含非法字符或不可访问
- **THEN** 系统应当显示错误消息："错误：商品文件路径无效或不可访问: {path}"
- **AND** 退出码应当为 1
- **AND** 提供路径格式示例

### Requirement: 商品输出模式用户配置
系统必须（MUST）在用户配置模型中支持商品输出相关的配置字段。

#### Scenario: 加载包含商品文件的配置
- **WHEN** 用户加载包含 `item_collect_file` 字段的配置文件
- **THEN** 系统应当成功解析该字段
- **AND** 将路径存储在 `UIConfig.item_collect_file` 属性中
- **AND** 支持绝对路径和相对路径（相对于配置文件目录）

#### Scenario: 商品文件字段缺失时的默认行为
- **WHEN** 用户配置文件中未包含 `item_collect_file` 字段
- **THEN** 系统应当将 `UIConfig.item_collect_file` 设置为 None
- **AND** 在 select-shops 模式下正常运行
- **AND** 在 select-goods 模式下触发验证错误

## MODIFIED Requirements

### Requirement: 模板数据生成
系统必须（MUST）提供命令行选项来生成不同选择模式的配置模板文件，帮助用户快速创建正确的配置。

#### Scenario: 生成 select-shops 模式模板
- **WHEN** 用户执行 `python cli/main.py create-template --mode select-shops`
- **THEN** 系统应当在当前目录生成 `user_data_template_select_shops.json` 文件
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
- **AND** 文件应当包含注释说明每个字段的用途

#### Scenario: 生成 select-goods 模式模板
- **WHEN** 用户执行 `python cli/main.py create-template --mode select-goods`
- **THEN** 系统应当在当前目录生成 `user_data_template_select_goods.json` 文件
- **AND** 文件应当包含以下字段及其默认值：
  - `good_shop_file`: "/path/to/good_shops.xlsx"
  - `item_collect_file`: "/path/to/item_collect.xlsx" **(新增)**
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
- **AND** 文件应当包含注释说明 `item_collect_file` 用于存储选品结果

#### Scenario: 指定输出路径
- **WHEN** 用户执行 `python cli/main.py create-template --mode select-shops --output /custom/path/my_template.json`
- **THEN** 系统应当在指定路径生成模板文件
- **AND** 如果目录不存在，应当自动创建

#### Scenario: 模式参数缺失
- **WHEN** 用户执行 `python cli/main.py create-template` 但未指定 `--mode`
- **THEN** 系统应当显示错误消息："错误：create-template 需要指定 --mode 参数（select-shops 或 select-goods）"
- **AND** 退出码应当为 1

#### Scenario: 模式参数无效
- **WHEN** 用户执行 `python cli/main.py create-template --mode invalid-mode`
- **THEN** 系统应当显示错误消息："错误：无效的模式 'invalid-mode'，可用模式：select-shops, select-goods"
- **AND** 退出码应当为 1

#### Scenario: 文件已存在
- **WHEN** 用户执行模板生成命令但目标文件已存在
- **THEN** 系统应当提示用户："文件已存在，是否覆盖？(y/n)"
- **AND** 如果用户输入 'y'，则覆盖文件
- **AND** 如果用户输入 'n'，则取消操作并退出
