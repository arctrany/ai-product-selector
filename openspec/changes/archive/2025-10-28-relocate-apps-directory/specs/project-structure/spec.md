## ADDED Requirements

### Requirement: Application Directory Structure
应用目录 SHALL 位于项目根目录下，以提供清晰的项目结构和便于管理。

#### Scenario: 应用目录位置
- **WHEN** 系统初始化应用管理器
- **THEN** 应用目录应位于项目根目录的 `apps/` 路径
- **AND** 系统应能正确加载该目录下的所有应用配置

#### Scenario: 路径解析
- **WHEN** 应用管理器解析应用路径
- **THEN** 系统应使用 `apps/` 作为默认应用目录
- **AND** 支持通过环境变量 `WORKFLOW_APPS_DIR` 覆盖默认路径

#### Scenario: 向后兼容性
- **WHEN** 系统检测到旧的应用目录结构 (`src_new/apps/`)
- **THEN** 系统应发出迁移警告
- **AND** 仍能正常加载旧位置的应用（临时兼容）

## ADDED Requirements

### Requirement: 应用路径配置管理
系统 SHALL 提供灵活的应用目录配置机制，支持不同部署环境的需求。

#### Scenario: 环境变量配置
- **WHEN** 设置环境变量 `WORKFLOW_APPS_DIR`
- **THEN** 系统应使用该变量指定的路径作为应用目录
- **AND** 路径可以是相对路径或绝对路径

#### Scenario: 配置文件指定
- **WHEN** 在配置文件中指定应用目录路径
- **THEN** 系统应优先使用配置文件中的设置
- **AND** 配置应支持环境变量展开

### Requirement: 应用配置格式优化
应用配置 SHALL 使用相对路径格式，避免硬编码的模块路径前缀。

#### Scenario: entry_point 配置格式
- **WHEN** 在 `app.json` 中配置工作流的 `entry_point`
- **THEN** 应使用相对路径格式 `"{app_name}.{flow_name}.imp.workflow_definition:function_name"`
- **AND** 系统应动态添加应用目录前缀进行模块解析

#### Scenario: 模块路径动态解析
- **WHEN** `AppManager` 加载工作流定义
- **THEN** 系统应根据当前应用目录配置动态构建完整的模块路径
- **AND** 支持通过环境变量 `WORKFLOW_APPS_DIR` 灵活配置应用目录

### Requirement: 函数注册机制增强
系统 SHALL 确保在新的目录结构下，工作流节点函数能正确注册和解析。

#### Scenario: 节点函数自动发现
- **WHEN** 加载工作流定义时
- **THEN** 系统应自动导入对应的节点模块（如 `nodes.py`）
- **AND** 确保 `@register_function` 装饰器正常执行

#### Scenario: 函数引用解析
- **WHEN** 工作流执行需要调用节点函数
- **THEN** 系统应能通过函数注册表正确找到对应的函数实现
- **AND** 函数调用应正常工作，不受路径变更影响