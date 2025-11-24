# cli Specification

## Purpose
TBD - created by archiving change add-item-shelf-days. Update Purpose after archive.
## Requirements
### Requirement: Item Shelf Days Configuration
The system SHALL accept item shelf days as a configurable parameter in user input data.

#### Scenario: Valid shelf days provided
- **WHEN** user provides item_created_days parameter in input data
- **THEN** the system uses this value for shelf time filtering

#### Scenario: Default shelf days used
- **WHEN** user does not provide item_created_days parameter in input data
- **THEN** the system uses a default value of 150 days for shelf time filtering

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
- **AND** 文件应当包含注释说明每个字段的用途

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
- **AND** 文件应当包含注释说明每个字段的用途

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

### Requirement: 用户数据加载
系统必须（MUST）从 JSON 文件加载用户配置，并应当（SHALL）忽略未识别的字段以保持向后兼容性。

#### Scenario: 加载包含已废弃字段的配置
- **WHEN** 用户加载包含 `item_created_days` 或 `category_blacklist` 的配置文件
- **THEN** 系统应当成功加载配置
- **AND** 显示警告消息提示这些字段已废弃
- **AND** 忽略 `item_created_days` 和 `category_blacklist` 字段
- **AND** 使用 `item_shelf_days` 字段（如果提供）或默认值

#### Scenario: 加载不完整的配置
- **WHEN** 用户加载的配置文件缺少某些可选字段
- **THEN** 系统应当使用默认值填充缺失的字段
- **AND** 成功加载配置

#### Scenario: output_path 未指定时使用默认值
- **WHEN** 用户加载的配置文件中 `output_path` 为空字符串或未提供
- **THEN** 系统应当将输出路径设置为当前工作目录
- **AND** 成功执行任务并将结果输出到当前目录

### Requirement: Selection Mode Flags
The system SHALL provide two mutually exclusive command-line flags to control the selection workflow mode.

#### Scenario: Select goods mode specified
- **WHEN** user provides `--select-goods` flag
- **THEN** the system skips store filtering and directly selects products from provided store list

#### Scenario: Select shops mode specified
- **WHEN** user provides `--select-shops` flag
- **THEN** the system performs store filtering and expansion (current behavior)

#### Scenario: No mode flag specified
- **WHEN** user does not provide either mode flag
- **THEN** the system defaults to select shops mode (`--select-shops`)

#### Scenario: Both mode flags specified
- **WHEN** user provides both `--select-goods` and `--select-shops` flags
- **THEN** the system SHALL reject the command with a clear error message indicating the flags are mutually exclusive

#### Scenario: Mode flags work with dryrun
- **WHEN** user provides a mode flag along with `--dryrun`
- **THEN** the system executes in the specified mode with dry-run behavior

### Requirement: Store Filter Configuration in User Data
The system SHALL accept store filtering thresholds as configurable parameters in user input data.

#### Scenario: User provides store filter thresholds
- **WHEN** user provides `min_store_sales_30days` and `min_store_orders_30days` in the `--data` JSON file
- **THEN** the system uses these values for store-level filtering in select-shops mode

#### Scenario: User omits store filter thresholds
- **WHEN** user does not provide store filter fields in the `--data` JSON file
- **THEN** the system uses default values (500,000 RUB for sales, 250 for orders)

#### Scenario: Invalid store filter values provided
- **WHEN** user provides negative or non-numeric values for store filter fields
- **THEN** the system rejects the configuration with a clear error message

#### Scenario: Store filters applied in select-shops mode
- **WHEN** running in `--select-shops` mode with user-provided store filter values
- **THEN** stores are filtered using the user-specified thresholds before product selection

#### Scenario: Store filters ignored in select-goods mode
- **WHEN** running in `--select-goods` mode
- **THEN** store filter thresholds are not applied (store filtering is skipped)

### Requirement: CLI层使用独立TaskManager
CLI模块 SHALL 重构以使用新的独立 task_manager 模块，替代原有分散的任务控制功能，实现清晰的职责分离。

#### Scenario: TaskController重构适配
- **WHEN** CLI的TaskController初始化时
- **THEN** 创建并使用 task_manager.TaskManager 实例而非直接管理任务状态
- **AND** 通过统一接口进行任务创建、启动、暂停、恢复、停止操作

#### Scenario: 状态管理职责分离
- **WHEN** CLI需要获取任务状态时
- **THEN** 通过TaskManager接口查询任务状态，而非直接访问内部状态变量
- **AND** UI状态管理器专注于界面状态，任务状态由TaskManager统一管理

#### Scenario: 适配器兼容现有接口
- **WHEN** 现有CLI代码调用原TaskController方法时
- **THEN** 通过适配器模式保持接口兼容性，内部委托给新的TaskManager
- **AND** 现有CLI调用代码无需修改即可正常工作

### Requirement: 增强的CLI命令处理
CLI模块 SHALL 提供增强的命令处理能力，利用新TaskManager的丰富功能提升用户体验。

#### Scenario: 任务状态查询命令
- **WHEN** 用户执行任务状态查询命令时
- **THEN** 通过TaskManager获取详细的任务信息：状态、进度、预估时间、统计数据
- **AND** 以用户友好的格式展示任务状态和进度信息

#### Scenario: 批量任务控制命令
- **WHEN** 用户执行批量控制命令时
- **THEN** 支持同时控制多个任务的启动、暂停、恢复、停止操作
- **AND** 提供批量操作的进度反馈和结果汇总

#### Scenario: 任务历史和统计命令
- **WHEN** 用户查看任务历史时
- **THEN** 展示任务执行历史、成功率、平均执行时间等统计信息
- **AND** 支持按时间、状态、类型等条件过滤任务历史

