## ADDED Requirements

### Requirement: 商品Excel写入器
系统必须（MUST）提供独立的商品Excel写入器，负责将商品分析结果写入标准化的Excel文件。

#### Scenario: 初始化商品Excel文件
- **WHEN** 创建 `ExcelProductWriter` 实例时提供商品文件路径
- **THEN** 系统应当验证文件路径有效性
- **AND** 如果文件不存在，创建新的Excel文件并写入表头
- **AND** 如果文件已存在，打开文件准备追加数据
- **AND** 表头应当包含：店铺ID、商品ID、商品名称、商品图片、绿标价格、黑标价格、佣金率、重量、长宽高、货源价格、利润率、预计利润

#### Scenario: 写入单个商品数据
- **WHEN** 调用 `write_product(product_result)` 方法
- **THEN** 系统应当将 `ProductAnalysisResult` 转换为Excel行数据
- **AND** 写入到下一个空行
- **AND** 所有数值字段应当格式化为正确的数据类型（数字、百分比）
- **AND** 价格字段保留2位小数
- **AND** 利润率字段显示为百分比（如 15.5%）

#### Scenario: 批量写入商品数据
- **WHEN** 调用 `batch_write_products(product_list)` 方法
- **THEN** 系统应当遍历所有商品并逐个写入
- **AND** 使用批量写入优化性能（每10条提交一次）
- **AND** 写入完成后自动保存文件
- **AND** 返回成功写入的商品数量

#### Scenario: 处理缺失字段
- **WHEN** 商品数据中某些字段为 None 或缺失
- **THEN** 系统应当使用默认值或空字符串填充
- **AND** 数值字段使用 0 作为默认值
- **AND** 字符串字段使用空字符串作为默认值
- **AND** 记录警告日志但不中断写入

#### Scenario: 写入失败时的错误处理
- **WHEN** 写入过程中发生错误（如磁盘空间不足、权限问题）
- **THEN** 系统应当记录错误日志（error级别）
- **AND** 错误日志应当包含详细的错误原因和失败的商品ID
- **AND** 单个商品写入失败不影响其他商品
- **AND** 继续处理后续商品，最后返回成功写入的数量

### Requirement: 商品输出流程集成
系统必须（MUST）在主流程中集成商品输出逻辑，根据选择模式决定输出目标。

#### Scenario: Select-Goods 模式输出商品
- **WHEN** 系统运行在 select-goods 模式且完成商品抓取和利润计算
- **THEN** 系统应当从所有 `StoreAnalysisResult` 中提取已筛选的利润达标商品
- **AND** 商品利润筛选已在 `_evaluate_products()` 中完成
- **AND** 为每个商品添加 `store_id` 字段
- **AND** 调用 `ExcelProductWriter.batch_write_products()` 写入商品Excel
- **AND** 同时更新店铺Excel状态列

#### Scenario: Select-Shops 模式保持原有行为
- **WHEN** 系统运行在 select-shops 模式
- **THEN** 系统应当按原有逻辑更新店铺Excel
- **AND** 不执行商品Excel写入操作
- **AND** 不初始化 `ExcelProductWriter`

#### Scenario: Dryrun 模式下的商品输出
- **WHEN** 系统运行在 dryrun 模式且选择 select-goods 模式
- **THEN** 系统应当执行完整的商品抓取和利润计算
- **AND** 模拟商品Excel写入操作（记录日志但不实际写入文件）
- **AND** 在日志中输出将要写入的商品数量和样例数据
- **AND** 显示 "🧪 试运行模式：模拟商品Excel写入" 提示

#### Scenario: 商品数据收集和转换
- **WHEN** 需要从 `StoreAnalysisResult` 列表中提取商品数据
- **THEN** 系统应当遍历所有店铺结果
- **AND** 提取每个店铺的 `products` 列表（已经是利润达标的商品）
- **AND** 为每个商品添加 `store_id` 字段（来自 store_data.store_id）
- **AND** 不包含跟卖信息（select-goods 模式下不抓取跟卖）
- **AND** 返回扁平化的商品列表

### Requirement: 商品数据模型定义
系统必须（MUST）定义商品Excel数据模型，确保数据结构标准化。

#### Scenario: 商品Excel数据类定义
- **WHEN** 在 `common/models/excel_models.py` 中定义 `ExcelProductData`
- **THEN** 数据类应当包含以下字段：
  - `store_id: str` - 店铺ID
  - `product_id: str` - 商品ID
  - `product_name: Optional[str]` - 商品名称
  - `image_url: Optional[str]` - 商品图片URL
  - `green_price: Optional[float]` - 绿标价格（卢布）
  - `black_price: Optional[float]` - 黑标价格（卢布）
  - `commission_rate: Optional[float]` - 佣金率
  - `weight: Optional[float]` - 重量（克）
  - `length: Optional[float]` - 长度（厘米）
  - `width: Optional[float]` - 宽度（厘米）
  - `height: Optional[float]` - 高度（厘米）
  - `source_price: Optional[float]` - 货源价格（人民币）
  - `profit_rate: Optional[float]` - 利润率
  - `profit_amount: Optional[float]` - 预计利润（人民币）
- **AND** 所有字段应当有类型注解
- **AND** 提供 `from_product_info()` 类方法，从 `ProductInfo` 和利润计算结果转换

#### Scenario: 商品数据验证
- **WHEN** 创建 `ExcelProductData` 实例
- **THEN** 系统应当验证必需字段不为空（`store_id`, `product_id`）
- **AND** 验证数值字段的合理范围（价格 > 0，利润率 -100% ~ 100%）
- **AND** 验证URL字段格式正确（如果提供）
- **AND** 如果验证失败，抛出 `DataValidationError`

### Requirement: 商品Excel配置
系统必须（MUST）在配置层提供商品Excel的列映射配置，支持灵活调整输出格式。

#### Scenario: 商品Excel列配置定义
- **WHEN** 在 `common/config/business_config.py` 的 `ExcelConfig` 中添加商品列配置
- **THEN** 应当定义以下配置字段：
  - `product_store_id_column: str = "A"` - 店铺ID列
  - `product_id_column: str = "B"` - 商品ID列
  - `product_name_column: str = "C"` - 商品名称列
  - `product_image_column: str = "D"` - 商品图片列
  - `product_green_price_column: str = "E"` - 绿标价格列
  - `product_black_price_column: str = "F"` - 黑标价格列
  - `product_commission_column: str = "G"` - 佣金率列
  - `product_weight_column: str = "H"` - 重量列
  - `product_dimensions_column: str = "I"` - 尺寸列（长宽高合并）
  - `product_source_price_column: str = "L"` - 货源价格列
  - `product_profit_rate_column: str = "M"` - 利润率列
  - `product_profit_amount_column: str = "N"` - 预计利润列
- **AND** 支持通过配置文件覆盖默认列位置

#### Scenario: 使用配置进行列映射
- **WHEN** `ExcelProductWriter` 写入数据时
- **THEN** 应当从 `ExcelConfig` 读取列配置
- **AND** 根据配置将数据写入对应的列
- **AND** 如果配置缺失，使用默认列位置

### Requirement: 跟卖逻辑跳过
系统必须（MUST）在 select-goods 模式下跳过跟卖数据抓取。

#### Scenario: Select-Goods 模式跳过跟卖
- **WHEN** 系统运行在 select-goods 模式
- **THEN** `_process_single_store()` 应当跳过 `_collect_competitor_stores()` 调用
- **AND** 不执行任何跟卖相关的抓取操作
- **AND** 仅抓取店铺自身的商品信息
