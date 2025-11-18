## ADDED Requirements

### Requirement: Selector Filter Configuration Naming
系统必须（SHALL）遵循统一的过滤器配置命名规范，以区分商品级别和店铺级别的过滤规则。

#### Scenario: 商品级别过滤器命名
- **WHEN** 定义商品级别的过滤配置时
- **THEN** 配置字段名称必须使用 `item_` 前缀
- **AND** 例如：`item_category_blacklist`、`item_min_weight`、`item_max_weight`

#### Scenario: 店铺级别过滤器命名
- **WHEN** 定义店铺级别的过滤配置时
- **THEN** 配置字段名称必须使用 `store_` 前缀
- **AND** 例如：`store_min_sales_30days`、`store_min_orders_30days`

#### Scenario: 选择器过滤配置类命名
- **WHEN** 定义过滤器配置类时
- **THEN** 类名应为 `SelectorFilterConfig`（而非 `StoreFilterConfig`）
- **AND** 配置对象应通过 `config.selector_filter` 访问

## MODIFIED Requirements

### Requirement: Product Category Blacklist Filtering
系统必须（SHALL）支持通过系统配置文件配置类目黑名单，用于过滤不符合要求的商品类目。

#### Scenario: 从系统配置读取类目黑名单
- **WHEN** 系统初始化 FilterManager 时
- **THEN** 应当从 `config.selector_filter.item_category_blacklist` 读取类目黑名单列表
- **AND** 如果配置文件中未提供，则使用默认黑名单列表

#### Scenario: 使用类目黑名单过滤商品
- **WHEN** 商品的中文类目或俄文类目包含黑名单关键词
- **THEN** 该商品应当被过滤掉
- **AND** 在 dryrun 模式下应当记录过滤原因

#### Scenario: 商品类目不在黑名单中
- **WHEN** 商品的中文类目和俄文类目都不包含黑名单关键词
- **THEN** 该商品应当通过类目过滤
- **AND** 继续执行其他过滤条件检查

#### Scenario: 空黑名单列表
- **WHEN** 系统配置中的 `item_category_blacklist` 为空列表
- **THEN** 不应用类目黑名单过滤
- **AND** 所有商品都通过类目过滤检查

#### Scenario: 向后兼容 - 用户数据中的类目黑名单（已废弃）
- **WHEN** 用户在 `--data` 文件中提供了 `category_blacklist` 字段
- **THEN** 系统应当显示废弃警告
- **AND** 忽略该字段
- **AND** 使用系统配置中的 `item_category_blacklist`

#### Scenario: 向后兼容 - 旧配置结构（store_filter）
- **WHEN** 系统配置文件使用旧的 `store_filter` 结构
- **THEN** 系统应当自动映射到新的 `selector_filter` 结构
- **AND** 显示迁移提示但不中断运行
