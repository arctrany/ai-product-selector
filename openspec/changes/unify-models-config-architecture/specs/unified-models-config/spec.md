# 独立模块化的统一模型与配置管理规范

## MODIFIED Requirements

### Requirement: 统一模型导入接口
系统SHALL提供统一的模型导入接口，消除重复定义和导入混乱，同时支持独立模块化架构。

#### Scenario: 模块独立化迁移
- **WHEN** 各模块创建独立的models.py文件
- **THEN** 每个模块的model类使用唯一前缀（Cli*, Task*, Common*）
- **AND** 模块间model完全独立，使用命名空间导入

#### Scenario: 消除ScrapingResult重复定义
- **WHEN** 发现ScrapingResult在多处定义
- **THEN** 统一在common/models.py中定义，其他模块通过导入使用
- **AND** 删除重复定义，保持唯一版本

#### Scenario: 向后兼容导入
- **WHEN** 现有代码使用旧的导入方式
- **THEN** 通过适配器转发到新的模块结构
- **AND** 功能行为与之前完全一致

## ADDED Requirements

### Requirement: RPA模块保护机制
系统SHALL确保RPA模块在架构重构过程中完全不受影响，保持其稳定性和成熟性。

#### Scenario: RPA模块完全隔离
- **WHEN** 进行架构重构时
- **THEN** RPA模块的所有文件保持原样不做任何更改
- **AND** RPA模块的导入方式和接口保持不变

#### Scenario: RPA依赖关系保护
- **WHEN** 其他模块需要使用RPA功能时
- **THEN** 继续使用现有的RPA模块接口
- **AND** 不将RPA模块纳入新的模块化架构体系

#### Scenario: RPA稳定性验证
- **WHEN** 重构完成后
- **THEN** RPA模块的所有功能和测试正常运行
- **AND** RPA模块与其他模块的依赖关系保持稳定

### Requirement: CLI/Task/Common模块冲突零容忍清理
系统SHALL彻底消除CLI、Task、Common三个模块间的所有配置重复、职责混乱和命名冲突，实现真正的零冲突架构。

#### Scenario: 配置重复完全清除
- **WHEN** 发现UIConfig与GoodStoreSelectorConfig参数重复时
- **THEN** 必须将重复参数统一到正确的模块中
- **AND** 消除所有新旧配置并存的情况（如BrowserConfig vs ScrapingConfig）
- **AND** 建立单一配置源，避免手动同步问题

#### Scenario: 模块职责严格分离
- **WHEN** 发现Common模块承担CLI/Task特定职责时
- **THEN** 必须将相关功能迁移到正确的模块中
- **AND** task_control相关功能迁移到Task模块
- **AND** CLI特定配置（dryrun、selection_mode）迁移到CLI模块
- **AND** 日志配置迁移到应用层

#### Scenario: 命名冲突彻底解决
- **WHEN** 发现字段命名冲突或语义重叠时
- **THEN** 必须统一命名规范，消除歧义
- **AND** browser/scraping字段冲突必须解决
- **AND** timeout相关参数必须规范化命名
- **AND** 重试参数必须统一命名

#### Scenario: 业务逻辑配置分离验证
- **WHEN** 检查配置类时
- **THEN** 不得包含业务计算规则或判定逻辑
- **AND** 价格计算规则必须从配置中分离到策略类
- **AND** 业务判定阈值必须通过策略模式管理

### Requirement: 独立模块化model和config支持
系统SHALL支持各独立模块(cli、task、common)拥有独立的models.py、config.py、config/目录，实现完全的模块化架构，同时保护RPA模块不受影响。

#### Scenario: 创建独立模块model文件
- **WHEN** 为CLI、Task、Common模块创建独立的models.py
- **THEN** 每个模块的model类使用唯一前缀（Cli*, Task*, Common*）
- **AND** 模块间model完全独立，无任何引用关系
- **AND** RPA模块保持现有结构不变

#### Scenario: 创建独立模块config文件  
- **WHEN** 为每个模块创建独立的config.py和config/目录
- **THEN** 每个模块的config类使用唯一前缀避免冲突
- **AND** 模块配置完全独立管理

#### Scenario: 零冲突保证验证
- **WHEN** 多个模块同时导入到同一文件中
- **THEN** 不出现任何命名冲突错误
- **AND** 每个类都可以通过模块前缀明确识别来源

### Requirement: 模块层级依赖管理
系统SHALL建立清晰的分层模块依赖架构，避免循环依赖和过度耦合。

#### Scenario: 建立分层依赖架构
- **WHEN** 设计模块间依赖关系
- **THEN** common为基础层(Level 1)，task为中间层(Level 2)，cli为应用层(Level 3)
- **AND** 高层模块可依赖低层模块，反之不可
- **AND** RPA模块作为独立稳定组件，不参与分层架构重构

#### Scenario: 避免循环依赖
- **WHEN** 模块间需要相互引用
- **THEN** 通过接口抽象或依赖注入解决循环依赖
- **AND** 任何时候都不出现import循环错误

#### Scenario: 共享组件管理
- **WHEN** 多个模块需要共享相同功能
- **THEN** 共享组件放置在common层
- **AND** 通过继承或组合方式复用，不直接复制代码

### Requirement: 命名冲突完全避免
系统SHALL采用双重策略（类名前缀+命名空间隔离）确保model和config绝对不发生命名冲突。

#### Scenario: 类名前缀策略实施
- **WHEN** 定义任何model或config类
- **THEN** 类名必须包含模块前缀（Cli*, Task*, Common*）
- **AND** 前缀命名规范一致，一目了然知道所属模块
- **AND** RPA模块保持现有命名规范不变

#### Scenario: 命名空间导入隔离
- **WHEN** 从不同模块导入类
- **THEN** 必须使用完整的模块路径导入（from cli.models import CliConfig）
- **AND** 禁止使用通配符导入（from module import *）

#### Scenario: 同文件多模块导入测试
- **WHEN** 在同一Python文件中导入多个模块的同类型类
- **THEN** 所有类可以正常使用，无任何名称冲突
- **AND** 代码可读性好，能清楚识别每个类的来源

### Requirement: 旧架构彻底清除
系统SHALL彻底清除旧架构文件和兼容机制，避免新旧两套并存的维护负担。

#### Scenario: 旧文件完全清除
- **WHEN** 迁移完成后
- **THEN** 完全删除common/models.py和common/config.py旧文件
- **AND** 移除所有向后兼容的转发机制

#### Scenario: 导入语句统一更新
- **WHEN** 清除旧架构时
- **THEN** 所有导入语句更新为新的命名空间格式
- **AND** 不保留任何旧的导入方式

#### Scenario: 平滑过渡测试
- **WHEN** 运行完整的测试套件
- **THEN** 所有现有测试用例100%通过
- **AND** 新增的模块化测试也全部通过

### Requirement: 配置层独立化管理
系统SHALL建立独立的配置管理体系，各模块配置完全独立且不产生冲突。

#### Scenario: 模块配置独立创建
- **WHEN** 为每个模块创建独立的config.py文件
- **THEN** 每个模块的配置类使用唯一前缀（CliConfig, TaskConfig, RpaConfig, CommonConfig）
- **AND** 配置类之间无任何继承或引用关系

#### Scenario: 配置命名空间隔离
- **WHEN** 从不同模块导入配置类
- **THEN** 使用完整的模块路径导入避免冲突
- **AND** 配置可以在同一文件中共存使用

#### Scenario: 配置验证独立性
- **WHEN** 各模块配置进行验证
- **THEN** 每个模块的配置验证逻辑完全独立
- **AND** 配置错误不会影响其他模块的配置

### Requirement: 工具函数模块化管理
系统SHALL将工具函数从模型文件中分离，按模块独立管理。

#### Scenario: 工具函数分离
- **WHEN** 模型文件包含工具函数
- **THEN** 工具函数迁移到各自模块的utils目录
- **AND** 保持原有功能不变

#### Scenario: 工具函数命名空间管理
- **WHEN** 不同模块有相似的工具函数
- **THEN** 通过模块前缀和命名空间避免冲突
- **AND** 函数调用路径清晰明确

#### Scenario: 工具函数共享机制
- **WHEN** 多个模块需要相同的工具函数
- **THEN** 共享工具函数放置在common/utils中
- **AND** 通过标准化接口提供给各模块使用
