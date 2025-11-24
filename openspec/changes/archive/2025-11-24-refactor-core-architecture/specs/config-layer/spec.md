## ADDED Requirements

### Requirement: 统一应用配置管理
系统SHALL提供统一的ApplicationConfig结构来管理所有配置信息，避免配置重复和不一致问题。

#### Scenario: 配置统一访问
- **WHEN** 任何组件需要配置信息时
- **THEN** SHALL通过ApplicationConfig统一接口获取
- **AND** 不允许直接访问UIConfig或GoodStoreSelectorConfig

#### Scenario: 配置字段映射
- **WHEN** UIConfig中的字段需要在业务层使用时
- **THEN** SHALL通过配置映射机制自动转换到对应的业务配置字段
- **AND** 重复字段SHALL被合并到统一的配置结构中

#### Scenario: 配置一致性验证
- **WHEN** 配置加载时
- **THEN** 系统SHALL验证配置的一致性和完整性
- **AND** 冲突的配置SHALL被检测并报告

## MODIFIED Requirements

### Requirement: CLI配置模型
UIConfig SHALL专注于CLI界面相关的配置参数，业务逻辑相关配置SHALL移入统一的ApplicationConfig中。

#### Scenario: CLI配置范围限制
- **WHEN** 定义UIConfig字段时
- **THEN** 只允许包含界面展示、用户输入、文件路径等CLI相关配置
- **AND** 业务逻辑配置SHALL被移除

#### Scenario: 配置转换接口
- **WHEN** UIConfig需要转换为业务配置时
- **THEN** SHALL使用标准的配置映射接口
- **AND** 转换过程SHALL是确定性和可测试的

## ADDED Requirements

### Requirement: CLI层logging配置接口一致性
CLI层logging配置接口SHALL与底层logging配置保持一致，确保参数名称和类型匹配，避免接口不匹配导致的运行时错误。

#### Scenario: CLI启动时正常调用logging配置
- **WHEN** CLI应用启动并初始化logging时
- **THEN** setup_logging函数调用SHALL成功
- **AND** 参数名称SHALL与函数定义保持一致

#### Scenario: CLI命令执行时logging正常工作  
- **WHEN** 执行CLI命令（status, start, stop, pause, resume）时
- **THEN** 所有日志输出SHALL正常显示
- **AND** 不应出现参数不匹配的TypeError

### Requirement: 配置参数简化管理
系统SHALL简化过度复杂的配置参数，移除未使用和过度设计的配置选项，提高系统的可维护性。

#### Scenario: 重试配置简化
- **WHEN** 系统需要重试机制时
- **THEN** SHALL使用简化的重试配置，仅保留基本的重试次数和延迟参数
- **AND** SHALL移除exponential_backoff、backoff_multiplier、max_backoff_delay_s等复杂参数

#### Scenario: 并发配置移除
- **WHEN** 配置系统性能参数时
- **THEN** SHALL移除max_concurrent_stores、max_concurrent_products等未实际使用的并发配置
- **AND** 系统SHALL采用顺序处理模式，简化架构设计

#### Scenario: 用户文件路径配置保留
- **WHEN** 用户通过--data参数提供文件路径时
- **THEN** good_shop_file、item_collect_file、margin_calculator等用户输入配置SHALL被保留
- **AND** 这些配置SHALL继续通过CLI界面正常传递和使用

## REMOVED Requirements

### Requirement: 过度复杂的重试退避配置
**Reason**: exponential_backoff、backoff_multiplier、max_backoff_delay_s等配置过度复杂，增加系统复杂度而无实际价值
**Migration**: 使用简化的重试机制，保留基本的重试次数和固定延迟

### Requirement: 未使用的并发配置参数
**Reason**: max_concurrent_stores、max_concurrent_products配置存在但系统未实际实现并发处理
**Migration**: 移除相关配置，系统采用顺序处理模式

### Requirement: 配置重复字段
**Reason**: 消除UIConfig和GoodStoreSelectorConfig之间的重复字段
**Migration**: 重复字段合并到ApplicationConfig的相应部分
